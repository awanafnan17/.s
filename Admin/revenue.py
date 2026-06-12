"""Revenue and late-fee calculation — single source of truth for financial metrics.

All money values use Decimal. All DB work uses ORM aggregation.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from Admin import models as admin_models

logger = logging.getLogger('crm.revenue')

ZERO = Decimal('0.00')


# ─────────────────────────────────────────────────────────────
#  Annotation helpers
# ─────────────────────────────────────────────────────────────

def annotate_students_with_totals(students_qs):
    """Annotate a Student queryset with total_paid_annotated to avoid N+1.

    Only counts confirmed, non-late-fee payments on active sessions.
    """
    return students_qs.annotate(
        total_paid_annotated=Coalesce(
            Sum(
                'student_sessions__student_payments__amount',
                filter=Q(
                    student_sessions__status='Active',
                    student_sessions__student_payments__payment_status='confirmed',
                    student_sessions__student_payments__is_late_fee_payment=False,
                    student_sessions__student_payments__amount__gt=ZERO,
                ),
            ),
            Value(ZERO),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
    )


# ─────────────────────────────────────────────────────────────
#  Late fee calculation
# ─────────────────────────────────────────────────────────────

def calculate_late_fee(student_session) -> Decimal:
    """Compute outstanding late fee owed for a single StudentSession.

    Rules:
      1. Skip if the session has no late_fee_amount configured.
      2. Skip if fee is fully paid (total_paid >= effective_fee).
      3. Skip if the session is fee-waived.
      4. Add late_fee_amount per overdue month past (due_day + grace_days).
      5. Cap at late_fee_maximum if configured (0 = no cap).
      6. Subtract late fees already collected (is_late_fee_payment=True, confirmed).
    """
    session_obj = student_session.session
    late_fee_amount: Decimal = session_obj.late_fee_amount or ZERO
    if late_fee_amount <= 0:
        return ZERO

    if getattr(student_session, 'is_fee_waived', False):
        return ZERO

    total_paid = student_session.session_paid
    effective_fee = student_session.session_total_fee
    if total_paid >= effective_fee:
        return ZERO

    enrollment_date = student_session.registration_date
    if not enrollment_date:
        return ZERO

    today = timezone.localdate()
    grace_days = session_obj.late_fee_grace_days or 0
    due_day = max(1, min(28, session_obj.due_day or 10))

    # Walk every month from enrollment to today, counting overdue ones.
    overdue_months = 0
    year, month = enrollment_date.year, enrollment_date.month
    while True:
        try:
            month_due_date = date(year, month, due_day)
        except ValueError:
            month_due_date = date(year, month, 28)
        grace_deadline = month_due_date + timedelta(days=grace_days)
        if grace_deadline > today:
            break
        overdue_months += 1
        # Advance one month
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1

    if overdue_months <= 0:
        return ZERO

    gross_late_fee = late_fee_amount * Decimal(overdue_months)

    cap = session_obj.late_fee_maximum or ZERO
    if cap > 0 and gross_late_fee > cap:
        gross_late_fee = cap

    # Subtract late fees already collected (or waived as paid).
    already_collected = admin_models.Payments.objects.filter(
        studentsession=student_session,
        is_late_fee_payment=True,
        payment_status='confirmed',
    ).aggregate(total=Coalesce(Sum('amount'), Value(ZERO), output_field=DecimalField(max_digits=12, decimal_places=2)))['total']

    remaining = gross_late_fee - (already_collected or ZERO)
    return max(ZERO, remaining)


# ─────────────────────────────────────────────────────────────
#  Revenue metrics
# ─────────────────────────────────────────────────────────────

def calculate_revenue_metrics(
    session_filter: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> dict:
    """Calculate dashboard metrics using ORM aggregation.

    All money values returned are Decimal-derived; ints in the dict are quantized
    rupee amounts (no fractional Rupees in display)."""
    today = timezone.localdate()

    payments_qs = admin_models.Payments.objects.select_related(
        'studentsession__student', 'studentsession__session', 'user'
    ).filter(payment_status='confirmed', amount__gt=ZERO)

    if date_from:
        payments_qs = payments_qs.filter(date__gte=date_from)
    if date_to:
        payments_qs = payments_qs.filter(date__lte=date_to)
    if session_filter:
        payments_qs = payments_qs.filter(studentsession__session_id=session_filter)

    # Non-late-fee revenue (the "real" revenue figure)
    revenue_qs = payments_qs.filter(is_late_fee_payment=False)
    revenue_agg = revenue_qs.aggregate(
        total_revenue=Coalesce(Sum('amount'), Value(ZERO), output_field=DecimalField(max_digits=14, decimal_places=2)),
        payment_count=Count('id'),
    )
    total_revenue: Decimal = revenue_agg['total_revenue']
    total_payments_count = revenue_agg['payment_count'] or 0

    # Late fee revenue
    late_fee_collected: Decimal = payments_qs.filter(is_late_fee_payment=True).aggregate(
        total=Coalesce(Sum('amount'), Value(ZERO), output_field=DecimalField(max_digits=14, decimal_places=2))
    )['total']

    # Student-level aggregates
    students = annotate_students_with_totals(
        admin_models.Student.objects.filter(status='Active').prefetch_related(
            'student_sessions__student_payments',
            'student_sessions__session',
        )
    )

    total_expected = ZERO
    total_pending = ZERO
    total_discount = ZERO
    total_paid_sum = ZERO
    students_paid = students_partial = students_unpaid = 0
    overdue_amount = ZERO
    overdue_students_count = 0
    late_fee_outstanding = ZERO
    student_fee_data = []

    for student in students:
        active_sessions = [ss for ss in student.student_sessions.all() if ss.status == 'Active']
        if not active_sessions:
            continue

        s_fee = student.total_fee
        s_paid = student.total_paid_annotated
        s_balance = max(ZERO, s_fee - s_paid)
        s_discount = sum((ss.discount or ZERO for ss in active_sessions), ZERO)
        s_late_fee = sum((calculate_late_fee(ss) for ss in active_sessions), ZERO)

        total_expected += s_fee
        total_paid_sum += s_paid
        total_pending += s_balance
        total_discount += s_discount
        late_fee_outstanding += s_late_fee

        if s_balance <= 0:
            status = 'Paid'
            students_paid += 1
        elif s_paid > 0:
            status = 'Partial'
            students_partial += 1
        else:
            status = 'Unpaid'
            students_unpaid += 1

        is_overdue = any(
            ss.due_date and ss.due_date < today and ss.session_balance > 0
            for ss in active_sessions
        )
        if is_overdue:
            overdue_amount += s_balance
            overdue_students_count += 1

        student_fee_data.append(
            _build_student_fee_obj(student, active_sessions, s_fee, s_paid, s_balance, s_discount, status, s_late_fee)
        )

    # Session revenue breakdown
    session_revenue_qs = revenue_qs.values('studentsession__session__session_name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    session_revenue = {item['studentsession__session__session_name']: item['total'] for item in session_revenue_qs}

    # User collection breakdown
    user_collection_qs = revenue_qs.values('user__first_name', 'user__last_name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    user_collection = {
        f"{item['user__first_name']} {item['user__last_name']}": item['total']
        for item in user_collection_qs
    }

    # Time-based revenue
    def _sum_for(filter_kwargs) -> Decimal:
        return revenue_qs.filter(**filter_kwargs).aggregate(
            total=Coalesce(Sum('amount'), Value(ZERO), output_field=DecimalField(max_digits=14, decimal_places=2))
        )['total']

    daily_revenue = _sum_for({'date': today})
    monthly_revenue = _sum_for({'date__year': today.year, 'date__month': today.month})
    yearly_revenue = _sum_for({'date__year': today.year})
    week_start = today - timedelta(days=today.weekday())
    weekly_revenue = _sum_for({'date__gte': week_start})

    # Derived
    total_students = len(student_fee_data)
    avg_payment = (total_revenue / total_payments_count) if total_payments_count > 0 else ZERO
    collection_rate = (total_revenue / total_expected * Decimal('100')) if total_expected > 0 else ZERO
    active_students_count = admin_models.Student.objects.filter(status='Active').count()
    revenue_per_student = (total_revenue / active_students_count) if active_students_count > 0 else ZERO

    days_elapsed = today.day
    if days_elapsed > 0 and monthly_revenue > 0:
        daily_avg = monthly_revenue / Decimal(days_elapsed)
        projected_monthly = monthly_revenue + daily_avg * Decimal(max(0, 30 - days_elapsed))
    else:
        projected_monthly = ZERO

    recent_payments = revenue_qs.order_by('-date', '-id')[:10]
    top_sessions = sorted(session_revenue.items(), key=lambda x: x[1], reverse=True)[:5]

    # Session performance
    session_performance = []
    for s_name, s_rev in session_revenue.items():
        s_obj = admin_models.Sessions.objects.filter(session_name=s_name).first()
        if s_obj:
            s_count = admin_models.StudentSession.objects.filter(session=s_obj, status='Active').count()
            session_performance.append({
                'name': s_name,
                'revenue': s_rev,
                'students': s_count,
                'avg_per_student': (s_rev / s_count) if s_count > 0 else ZERO,
            })
    session_performance.sort(key=lambda x: x['revenue'], reverse=True)

    return {
        'student_fees': student_fee_data,
        'total_revenue': int(total_revenue),
        'total_pending': int(total_pending),
        'total_discount': int(total_discount),
        'total_expected_revenue': int(total_expected),
        'session_revenue': session_revenue,
        'user_collection': user_collection,
        'total_payments_count': total_payments_count,
        'recent_payments': recent_payments,
        'top_sessions': top_sessions,
        'avg_payment': int(avg_payment.quantize(Decimal('1'))),
        'collection_rate': float(collection_rate.quantize(Decimal('0.1'))),
        'students_paid': students_paid,
        'students_partial': students_partial,
        'students_unpaid': students_unpaid,
        'total_students': total_students,
        'overdue_amount': int(overdue_amount),
        'daily_revenue': daily_revenue,
        'yearly_revenue': yearly_revenue,
        'monthly_revenue': monthly_revenue,
        'weekly_revenue': weekly_revenue,
        'active_students_count': active_students_count,
        'revenue_per_student': int(revenue_per_student.quantize(Decimal('1'))),
        'overdue_students_count': overdue_students_count,
        'projected_monthly_revenue': int(projected_monthly.quantize(Decimal('1'))),
        'session_performance': session_performance,
        'late_fee_collected': late_fee_collected,
        'late_fee_outstanding': int(late_fee_outstanding),
        'total_outstanding': int(total_pending + late_fee_outstanding),
        'today_date': today,
    }


def _build_student_fee_obj(student, sessions_list, total_fee, paid, balance, discount, status, late_fee):
    """Build a display-only object for templates."""
    return type('StudentFee', (), {
        'student': student,
        'sessions': sessions_list,
        'calculated_final_fee': int(total_fee),
        'display_paid_amount': int(paid),
        'calculated_remaining_amount': int(balance),
        'display_discount': int(discount),
        'payment_status': status,
        'late_fee_owed': int(late_fee),
    })()


def calculate_student_balance(student_session_id: int) -> dict:
    """Return balance details for a specific student session."""
    try:
        ss = admin_models.StudentSession.objects.select_related('student', 'session').prefetch_related(
            'student_payments'
        ).get(id=student_session_id)
    except admin_models.StudentSession.DoesNotExist:
        return {'error': 'Student session not found'}

    return {
        'session_total_fee': ss.session_total_fee,
        'session_paid': ss.session_paid,
        'session_balance': ss.session_balance,
        'is_primary': ss.is_primary_session,
        'late_fee_owed': calculate_late_fee(ss),
    }

from django import forms
from authentication.models import User
from Admin.models import Sessions, Student, Lead, Attendance


class UserForm(forms.ModelForm):
    """User form that automatically hashes passwords on save."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'usertype', 'status', 'mobile_no', 'cnic', 'address', 'profile_photo', 'joining_date']
        widgets = {
            'password': forms.PasswordInput(render_value=True),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        # Hash password if it was changed (not already hashed)
        raw_password = self.cleaned_data.get('password', '')
        if raw_password and ('$' not in raw_password or len(raw_password) < 50):
            user.set_password(raw_password)
        if commit:
            user.save()
        return user

class SessionForm(forms.ModelForm):
    class Meta:
        model = Sessions
        fields = [
            'session_name', 'session_type', 'start_date', 'end_date',
            'session_photo', 'registration_fee', 'fee', 'status',
            'late_fee_amount', 'late_fee_grace_days', 'late_fee_maximum', 'due_day',
        ]
        widgets = {
            'session_type': forms.Select(attrs={'class': 'form-select', 'onchange': 'toggleFeeFields()'}),
            'session_name': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'late_fee_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'late_fee_grace_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'late_fee_maximum': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'due_day': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 28}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        fee = cleaned_data.get('fee')
        
        if not fee:
            raise forms.ValidationError({'fee': 'Fee is required for all sessions.'})
            
        return cleaned_data

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        exclude = [
            'created_at', 'updated_at', 'rollno', 'added_by',
            'deleted_at', 'deleted_by',
        ]
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists (excluding current instance if editing)
            existing = Student.objects.filter(email=email)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError("A student with this email already exists.")
        return email
        
    def clean_cnic(self):
        cnic = self.cleaned_data.get('cnic')
        if cnic:
            # Remove any non-digit characters for validation
            cnic_digits = ''.join(filter(str.isdigit, cnic))
            if len(cnic_digits) != 13:
                raise forms.ValidationError("CNIC must contain exactly 13 digits.")
        return cnic

class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            'name', 'email', 'mobile_no', 'area_of_residence',
            'session', 'form_of_inquiry',
        ]

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['course', 'student', 'date', 'status']
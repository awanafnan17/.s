from django.test import SimpleTestCase
from datetime import date, timedelta
from Admin.views import build_due_payment_session
from Admin.pdf_parser import (
    FORMAT_NAME_ONLY,
    FORMAT_WITH_FATHER,
    detect_pdf_format,
    extract_candidates,
)

class DummySession:
    def __init__(self, total, paid, balance):
        self.session_total_fee = total
        self.session_paid = paid
        self.session_balance = balance
        self.student = type('S', (), {})()
        self.session = type('Sess', (), {})()

class DummyPayment:
    def __init__(self, ss, d, pid=1):
        self.studentsession = ss
        self.date = d
        self.id = pid

class CalculationTests(SimpleTestCase):
    def test_build_due_payment_session_calculates_fields(self):
        total = 65000
        paid = 12500
        balance = total - paid
        ss = DummySession(total, paid, balance)
        p = DummyPayment(ss, date.today())
        obj = build_due_payment_session(p, date.today())
        self.assertEqual(obj.fee_amount, total)
        self.assertEqual(obj.fee_paid, paid)
        self.assertEqual(obj.balance, balance)


FPSC_TEXT = """
FEDERAL PUBLIC SERVICE COMMISSION
ANNEX-A
Merit No. Roll No. Name of Candidate Domicile Group Remarks
1 12345 AYESHA SIDDIQUA Punjab General Qualified
2 23456 HAFIZ MUHAMMAD ZEESHAN
ALTAF Punjab General Qualified
3 34567 ALI RAZA Sindh Minority Qualified
Page 1 of 2
4 45678 FATIMA NOOR KPK Women Qualified
"""

PPSC_SO_TEXT = """
PUNJAB PUBLIC SERVICE COMMISSION
Merit No. App No. Name of Candidate with Father's Name Domicile
1 PPSC-991 ALI RAZA S/O MUHAMMAD ASLAM Punjab
2 PPSC-992 AYESHA SIDDIQUA D/O ABDUL GHAFFAR Punjab
3 PPSC-993 HAFIZ MUHAMMAD ZEESHAN S/O ALTAF
HUSSAIN Punjab
"""

ECP_COLUMNS_TEXT = """
ELECTION COMMISSION OF PAKISTAN
S# Roll # Name Father Name Domicile
1 501 ALI RAZA MUHAMMAD ASLAM Punjab
2 502 FATIMA NOOR GHULAM RASOOL Sindh
"""


class PdfParserTests(SimpleTestCase):
    def test_detects_fpsc_name_only_format(self):
        self.assertEqual(detect_pdf_format(FPSC_TEXT), FORMAT_NAME_ONLY)

    def test_detects_father_name_formats(self):
        self.assertEqual(detect_pdf_format(PPSC_SO_TEXT), FORMAT_WITH_FATHER)
        self.assertEqual(detect_pdf_format(ECP_COLUMNS_TEXT), FORMAT_WITH_FATHER)

    def test_fpsc_extracts_names_and_joins_wrapped_lines(self):
        candidates = extract_candidates(FPSC_TEXT)
        names = [c['name'] for c in candidates]
        self.assertEqual(names, [
            'AYESHA SIDDIQUA',
            'HAFIZ MUHAMMAD ZEESHAN ALTAF',
            'ALI RAZA',
            'FATIMA NOOR',
        ])
        self.assertTrue(all(c['father_name'] is None for c in candidates))
        self.assertEqual(candidates[0]['roll_no'], '12345')

    def test_ppsc_splits_name_and_father_on_so_marker(self):
        candidates = extract_candidates(PPSC_SO_TEXT)
        self.assertEqual(candidates[0]['name'], 'ALI RAZA')
        self.assertEqual(candidates[0]['father_name'], 'MUHAMMAD ASLAM')
        # Wrapped father name continues onto the next line.
        self.assertEqual(candidates[2]['name'], 'HAFIZ MUHAMMAD ZEESHAN')
        self.assertEqual(candidates[2]['father_name'], 'ALTAF HUSSAIN')

    def test_ecp_columns_keep_combined_blob_for_subset_matching(self):
        candidates = extract_candidates(ECP_COLUMNS_TEXT)
        self.assertEqual(candidates[0]['combined'], 'ALI RAZA MUHAMMAD ASLAM')
        self.assertEqual(candidates[1]['combined'], 'FATIMA NOOR GHULAM RASOOL')

    def test_header_and_page_lines_are_not_candidates(self):
        candidates = extract_candidates(FPSC_TEXT)
        self.assertEqual(len(candidates), 4)

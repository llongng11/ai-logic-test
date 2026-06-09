import unittest
from calculator import PolicyBenefitsCalculator

class TestPolicyBenefitsCalculator(unittest.TestCase):
    def setUp(self):
        # Thiết lập cấu hình giả lập gọn nhẹ phục vụ test đơn vị
        self.policy_data = {
            "policy_id": "TEST-POL",
            "effective_date": "2024-01-01",
            "annual_limit": 10000,
            "deductible": 1000,
            "benefits": {
                "OUTPATIENT": {"per_visit_limit": 2000, "copay_percentage": 0.20, "waiting_period_days": 0},
                "INPATIENT": {"per_visit_limit": 10000, "copay_percentage": 0.0, "waiting_period_days": 30}
            },
            "exclusions": ["Cosmetic Surgery"]
        }

    def test_01_deductible_first_claim(self):
        """1. Thử thách Khấu trừ: Hóa đơn đầu tiên khách phải tự trả hết để kích hoạt gói"""
        calc = PolicyBenefitsCalculator(self.policy_data)
        res = calc.calculate_single_expense({
            "expense_id": "T1", "date": "2024-01-05", "benefit_type": "OUTPATIENT", "amount": 600, "diagnosis": "Flu"
        })
        self.assertEqual(res["covered_amount"], 0)
        self.assertEqual(res["member_pays"], 600)
        self.assertEqual(calc.accumulated_deductible, 600)

    def test_02_waiting_period_denial(self):
        """2. Thử thách Thời gian chờ: Từ chối thẳng nếu đi nằm viện quá sớm"""
        calc = PolicyBenefitsCalculator(self.policy_data)
        res = calc.calculate_single_expense({
            "expense_id": "T2", "date": "2024-01-10", "benefit_type": "INPATIENT", "amount": 5000, "diagnosis": "Fever"
        })
        self.assertEqual(res["decision"], "DENIED")
        self.assertTrue("Waiting period" in res["reason"])

    def test_03_exclusion_denial(self):
        """3. Thử thách Danh mục loại trừ: Từ chối bệnh cấm"""
        calc = PolicyBenefitsCalculator(self.policy_data)
        res = calc.calculate_single_expense({
            "expense_id": "T3", "date": "2024-02-01", "benefit_type": "OUTPATIENT", "amount": 2000, "diagnosis": "Cosmetic Surgery"
        })
        self.assertEqual(res["decision"], "DENIED")
        self.assertTrue("exclusions" in res["reason"])

    def test_04_copay_application(self):
        """4. Thử thách Co-pay: Đã qua khấu trừ, hóa đơn phải chia tỷ lệ 80/20 chuẩn xác"""
        calc = PolicyBenefitsCalculator(self.policy_data)
        calc.accumulated_deductible = 1000 
        res = calc.calculate_single_expense({
            "expense_id": "T4", "date": "2024-02-01", "benefit_type": "OUTPATIENT", "amount": 1000, "diagnosis": "Flu"
        })
        self.assertEqual(res["covered_amount"], 800)
        self.assertEqual(res["copay_amount"], 200)
        self.assertEqual(res["member_pays"], 200)

    def test_05_visit_limit_capping(self):
        """5. Thử thách Cắt ngọn lần khám: Vượt trần lần khám bắt buộc phải cắt gọt trước khi tính Co-pay"""
        calc = PolicyBenefitsCalculator(self.policy_data)
        calc.accumulated_deductible = 1000
        res = calc.calculate_single_expense({
            "expense_id": "T5", "date": "2024-02-01", "benefit_type": "OUTPATIENT", "amount": 3000, "diagnosis": "Flu"
        })
        self.assertEqual(res["covered_amount"], 1600) # (Trần 2000 - 20% Copay = 1600)
        self.assertEqual(res["member_pays"], 1400)   # (400 Copay + 1000 phần vượt trần)

    def test_06_annual_limit_exhaustion(self):
        """6. Thử thách Ví cạn: Khi ví năm bằng 0, từ chối mọi yêu cầu tiếp theo"""
        calc = PolicyBenefitsCalculator(self.policy_data)
        calc.remaining_annual_limit = 0
        res = calc.calculate_single_expense({
            "expense_id": "T6", "date": "2024-02-01", "benefit_type": "OUTPATIENT", "amount": 500, "diagnosis": "Flu"
        })
        self.assertEqual(res["decision"], "DENIED")

    def test_07_partial_annual_limit_capping(self):
        """7. Thử thách Cắt ngọn ví năm: Ví còn ít hơn tiền định trả, chỉ trả nốt phần còn lại"""
        calc = PolicyBenefitsCalculator(self.policy_data)
        calc.accumulated_deductible = 1000
        calc.remaining_annual_limit = 500  
        res = calc.calculate_single_expense({
            "expense_id": "T7", "date": "2024-02-01", "benefit_type": "OUTPATIENT", "amount": 1000, "diagnosis": "Flu"
        })
        self.assertEqual(res["covered_amount"], 500)
        self.assertEqual(res["remaining_annual_limit"], 0)

    def test_08_invalid_benefit_type(self):
        """8. Thử thách Quyền lợi lạ: Từ chối nếu quyền lợi không đăng ký trong gói"""
        calc = PolicyBenefitsCalculator(self.policy_data)
        res = calc.calculate_single_expense({
            "expense_id": "T8", "date": "2024-02-01", "benefit_type": "VISION", "amount": 1000, "diagnosis": "Myopia"
        })
        self.assertEqual(res["decision"], "DENIED")

    def test_09_multiple_claims_deductible_progression(self):
        """9. Thử thách Chuỗi Khấu trừ: Hai hóa đơn liên tiếp cùng đắp vào cho đủ mức khấu trừ"""
        calc = PolicyBenefitsCalculator(self.policy_data)
        res1 = calc.calculate_single_expense({"expense_id": "M1", "date": "2024-01-05", "benefit_type": "OUTPATIENT", "amount": 700, "diagnosis": "Flu"})
        res2 = calc.calculate_single_expense({"expense_id": "M2", "date": "2024-01-06", "benefit_type": "OUTPATIENT", "amount": 500, "diagnosis": "Flu"})
        
        self.assertEqual(res1["covered_amount"], 0) # Ăn trọn 700 khấu trừ
        self.assertEqual(res2["covered_amount"], 160) # Gánh nốt 300 khấu trừ, còn lại 200 tính bảo hiểm (200 - 20% Copay = 160)

    def test_10_zero_copay_coverage(self):
        """10. Thử thách Trả trọn 100%: Gói Inpatient có Copay 0% nên phải trả trọn vẹn hóa đơn"""
        calc = PolicyBenefitsCalculator(self.policy_data)
        calc.accumulated_deductible = 1000
        res = calc.calculate_single_expense({
            "expense_id": "T10", "date": "2024-02-15", "benefit_type": "INPATIENT", "amount": 4000, "diagnosis": "Pneumonia"
        })
        self.assertEqual(res["covered_amount"], 4000)
        self.assertEqual(res["member_pays"], 0)

if __name__ == "__main__":
    unittest.main()
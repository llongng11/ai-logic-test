import json
from datetime import datetime

class PolicyBenefitsCalculator:
    def __init__(self, policy_data):
        self.policy_id = policy_data["policy_id"]
        self.effective_date = datetime.strptime(policy_data["effective_date"], "%Y-%m-%d")
        self.remaining_annual_limit = policy_data["annual_limit"]
        self.deductible_target = policy_data["deductible"]
        self.accumulated_deductible = 0
        self.benefits = policy_data["benefits"]
        self.exclusions = policy_data["exclusions"]

    def process_expenses(self, expenses):
        # Đề bài bắt buộc xử lý theo thứ tự thời gian tuyến tính
        sorted_expenses = sorted(expenses, key=lambda x: x["date"])
        results = []
        for exp in sorted_expenses:
            results.append(self.calculate_single_expense(exp))
        return results

    def calculate_single_expense(self, exp):
        exp_id = exp["expense_id"]
        exp_date = datetime.strptime(exp["date"], "%Y-%m-%d")
        b_type = exp["benefit_type"]
        amount = exp["amount"]
        diagnosis = exp["diagnosis"]

        # Khởi tạo Object kết quả mặc định (Giả định bị từ chối)
        res = {
            "expense_id": exp_id,
            "submitted_amount": amount,
            "covered_amount": 0,
            "copay_amount": 0,
            "member_pays": amount,
            "decision": "DENIED",
            "reason_id": "DEFAULT_DENIED",  # Quản lý mã lỗi cố định
            "reason": "",
            "remaining_annual_limit": int(self.remaining_annual_limit)
        }

        # 🚪 CỬA 1: KIỂM TRA DANH MỤC LOẠI TRỪ & THỜI GIAN CHỜ
        if diagnosis in self.exclusions:
            res["reason_id"] = "EXCLUSION_DENIED"
            res["reason"] = f"[Từ chối] Chẩn đoán '{diagnosis}' nằm trong danh mục loại trừ của hợp đồng."
            return res

        if b_type not in self.benefits:
            res["reason_id"] = "BENEFIT_TYPE_NOT_COVERED"
            res["reason"] = f"[Từ chối] Quyền lợi nhóm '{b_type}' không được hỗ trợ trong gói bảo hiểm này."
            return res

        b_config = self.benefits[b_type]
        days_elapsed = (exp_date - self.effective_date).days
        if days_elapsed < b_config["waiting_period_days"]:
            res["reason_id"] = "WAITING_PERIOD_DENIED"
            res["reason"] = f"[Từ chối] Thời gian chờ cho nhóm {b_type} là {b_config['waiting_period_days']} ngày (Hiện mới trải qua {days_elapsed} ngày)."
            return res

        # 🚪 CỬA 2: KIỂM TRA HẠN MỨC NĂM CÒN LẠI (Nếu cạn về 0 thì khóa sổ)
        if self.remaining_annual_limit <= 0:
            res["reason_id"] = "ANNUAL_LIMIT_EXHAUSTED"
            res["reason"] = "[Từ chối] Hạn mức chi trả tối đa theo năm của hợp đồng đã cạn kiệt hoàn toàn."
            return res

        current_base = amount
        member_deductible_share = 0

        # 🚪 CỬA 3: ÁP DỤNG MỨC KHẤU TRỪ (Deductible)
        if self.accumulated_deductible < self.deductible_target:
            needed = self.deductible_target - self.accumulated_deductible
            if current_base <= needed:
                member_deductible_share = current_base
                self.accumulated_deductible += current_base
                current_base = 0
            else:
                member_deductible_share = needed
                self.accumulated_deductible = self.deductible_target
                current_base -= needed

        # Nếu toàn bộ số tiền hóa đơn bị nuốt gọn bởi mức khấu trừ
        if current_base == 0:
            res["decision"] = "PARTIALLY_COVERED" if amount > member_deductible_share else "DENIED"
            res["reason_id"] = "DEDUCTIBLE_ABSORBED"
            res["reason"] = f"[Khấu trừ đầu năm] Khách hàng tự thanh toán {member_deductible_share:,} THB để tích lũy mức khấu trừ."
            res["member_pays"] = amount
            return res

        # 🚪 CỬA 4: ÁP DỤNG GIỚI HẠN MỖI LẦN KHÁM (Per-Visit Sub-limit)
        visit_limit = b_config["per_visit_limit"]
        reduced_by_visit = False
        excess_visit_amount = 0
        if current_base > visit_limit:
            excess_visit_amount = current_base - visit_limit
            current_base = visit_limit
            reduced_by_visit = True

        # 🚪 CỬA 5: ÁP DỤNG TỶ LỆ ĐỒNG CHI TRẢ (Co-payment %)
        copay_pct = b_config["copay_percentage"]
        copay_money = current_base * copay_pct
        insurance_share = current_base - copay_money

        # 🚪 CỬA 6: CẮT NGỌN THEO TRẦN HẠN MỨC NĂM CÒN LẠI (Annual Limit Capping)
        reduced_by_annual = False
        if insurance_share > self.remaining_annual_limit:
            insurance_share = self.remaining_annual_limit
            reduced_by_annual = True

        # Cập nhật trạng thái ví tiền của hợp đồng
        self.remaining_annual_limit -= insurance_share

        # Tính toán chi phí phân bổ thực tế cuối cùng
        final_member_pays = member_deductible_share + copay_money + excess_visit_amount
        if reduced_by_annual:
            # Nếu quỹ bảo hiểm cạn, phần hụt bảo hiểm không trả nổi khách phải tự gánh nốt
            final_member_pays += (current_base - copay_money) - insurance_share

        # Xác định trạng thái Decision
        if insurance_share == 0:
            res["decision"] = "DENIED"
        elif insurance_share < amount:
            res["decision"] = "PARTIALLY_COVERED"
        else:
            res["decision"] = "FULLY_COVERED"

        # Định vị Mã ID xử lý tổng hợp chính dựa trên kịch bản dòng tiền đi qua
        if reduced_by_annual:
            res["reason_id"] = "ANNUAL_LIMIT_CAPPED"
        elif reduced_by_visit and copay_money > 0:
            res["reason_id"] = "VISIT_LIMIT_AND_COPAY_APPLIED"
        elif reduced_by_visit:
            res["reason_id"] = "VISIT_LIMIT_CAPPED"
        elif copay_money > 0:
            res["reason_id"] = "COPAY_APPLIED"
        else:
            res["reason_id"] = "STANDARD_FULLY_COVERED"

        # Text hỗ trợ log
        reasons = []
        if member_deductible_share > 0:
            reasons.append(f"Tích lũy khấu trừ đạt chỉ tiêu thêm {int(member_deductible_share):,} THB.")
        if reduced_by_visit:
            reasons.append(f"Chạm trần giới hạn lần khám (Giữ lại tối đa {visit_limit:,} THB để tính tiền).")
        if copay_money > 0:
            reasons.append(f"Áp dụng đồng chi trả {int(copay_pct*100)}%.")
        if reduced_by_annual:
            reasons.append("Cắt giảm chi trả do quỹ bảo hiểm năm sắp cạn kiệt.")
        if not reasons:
            reasons.append("Chi trả trọn gói theo điều khoản tiêu chuẩn.")

        res["covered_amount"] = int(insurance_share)
        res["copay_amount"] = int(copay_money)
        res["member_pays"] = int(final_member_pays)
        res["reason"] = " ".join(reasons)
        res["remaining_annual_limit"] = int(self.remaining_annual_limit)

        return res

    def get_summary(self):
        return {
            "remaining_annual_limit": int(self.remaining_annual_limit),
            "accumulated_deductible": int(self.accumulated_deductible),
            "deductible_satisfied": self.accumulated_deductible >= self.deductible_target
        }
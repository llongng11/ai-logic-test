import json
from calculator import PolicyBenefitsCalculator

def main():
    # 1. Đọc dữ liệu luật bảo hiểm từ file policy.json
    with open("policy.json", "r", encoding="utf-8") as f:
        policy_data = json.load(f)
        
    # 2. Đọc danh sách 20 hóa đơn từ file expenses.json vừa tạo
    with open("expenses.json", "r", encoding="utf-8") as f:
        expenses_data = json.load(f)
        
    # 3. Khởi chạy Cỗ máy tính toán
    calculator = PolicyBenefitsCalculator(policy_data)
    processed_results = calculator.process_expenses(expenses_data)
    
    ## Từ điển việt hoá thông tin
    vietnamese_decision = {
        "FULLY_COVERED": "CHẤP THUẬN TOÀN BỘ (FULLY_COVERED)",
        "PARTIALLY_COVERED": "CHẤP THUẬN MỘT PHẦN (PARTIALLY_COVERED)",
        "DENIED": "TỪ CHỐI (DENIED)"
    }
    
    # 4. In bảng log kết quả ra màn hình terminal
    print("\n" + "="*85)
    print("             BẢO HIỂM PAPAYA - NHẬT KÝ HỆ THỐNG XỬ LÝ BỒI THƯỜNG TỰ ĐỘNG")
    print("="*85)
    
    for res in processed_results:
        vn_decision = vietnamese_decision.get(res['decision'], res['decision'])
        
        print(f"[{res['expense_id']}] Số tiền nộp: {res['submitted_amount']:,} THB | Bảo hiểm trả: {res['covered_amount']:,} THB | Khách trả: {res['member_pays']:,} THB")
        print(f"  -> Quyết định: {vn_decision}")
        print(f"  -> Mã nghiệp vụ (Reason ID): {res['reason_id']}")
        print(f"  -> Lý do chi tiết: {res['reason']}")
        print(f"  -> Hạn mức năm còn lại của hợp đồng: {res['remaining_annual_limit']:,} THB")
        print("-" * 85)
        
    summary = calculator.get_summary()
    print("\n" + "="*85)
    print("                       BÁO CÁO TỔNG KẾT QUYỀN LỢI HỢP ĐỒNG CUỐI NĂM")
    print("="*85)
    print(f" • Hạn mức quỹ bảo hiểm còn lại cuối năm : {summary['remaining_annual_limit']:,} THB")
    print(f" • Mức khấu trừ đã tích lũy của khách    : {summary['accumulated_deductible']:,}/1,000 THB")
    print(f" • Trạng thái hoàn thành mức khấu trừ    : {'ĐÃ ĐẠT CHỈ TIÊU' if summary['deductible_satisfied'] else 'CHƯA ĐỦ'}")
    print("="*85 + "\n")

if __name__ == "__main__":
    main()
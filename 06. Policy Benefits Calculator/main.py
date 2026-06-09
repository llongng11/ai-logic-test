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
    
    # 4. In bảng log kết quả ra màn hình terminal
    print("\n" + "="*85)
    print("                 PAPAYA INSURANCE - AUTOMATED CLAIMS ENGINE LOG")
    print("="*85)
    
    for res in processed_results:
        print(f"[{res['expense_id']}] Submitted: {res['submitted_amount']} THB | Covered: {res['covered_amount']} THB | Member Pays: {res['member_pays']} THB")
        print(f"  -> Decision: {res['decision']}")
        print(f"  -> Explanation Reason: {res['reason']}")
        print(f"  -> Remaining Policy Annual Limit: {res['remaining_annual_limit']} THB")
        print("-" * 85)
        
    summary = calculator.get_summary()
    print("\n" + "="*85)
    print("                       FINAL POLICY BENEFIT SUMMARY REPORT")
    print("="*85)
    print(f" • Remaining Annual Policy Balance : {summary['remaining_annual_limit']} THB")
    print(f" • Accumulated Member Deductible   : {summary['accumulated_deductible']}/1000 THB")
    print(f" • Deductible Status Satisfied     : {summary['deductible_satisfied']}")
    print("="*85 + "\n")

if __name__ == "__main__":
    main()
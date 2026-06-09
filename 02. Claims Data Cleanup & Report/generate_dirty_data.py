import csv
import random

def generate_dirty_dataset(filename="claims_dirty.csv"):
    """
    Sinh ra file dữ liệu bảo hiểm CHÍNH XÁC 500 DÒNG (bao gồm cả dòng lỗi và dòng trùng lặp).
    Tỷ lệ phân bổ các giá trị lỗi được chia đều để tăng tính thử thách cho bài toán.
    """
    random.seed(42)  # Đảm bảo dữ liệu sinh ra cố định mỗi lần chạy
    
    diagnoses_pool = ["Flu", "Acute bronchitis", "Gastritis", "Migraine", "Back pain", "Appendicitis", "Allergy", "Toothache"]
    claim_types_pool = ["OUTPATIENT", "INPATIENT", "DENTAL"]
    statuses_pool = ["APPROVED", "REJECTED", "PENDING", "IN_REVIEW"]
    
    header = ["claim_id", "policy_id", "member_name", "claim_type", "diagnosis", "submitted_amount", "currency", "submitted_date", "status"]
    
    # Định nghĩa trước số lượng dòng trùng lặp và dòng lỗi để khống chế tổng 500 dòng
    total_target_rows = 500
    exact_duplicates_count = 10  # Sẽ có 10 dòng bị nhân bản y chang
    unique_rows_count = total_target_rows - exact_duplicates_count # 490 dòng độc nhất
    
    rows = []
    
    for i in range(1, unique_rows_count + 1):
        # 1. Khởi tạo dữ liệu nền chuẩn và sạch trước
        claim_id = f"CLM-{str(i).zfill(5)}"
        policy_id = f"POL-{1000 + i}"
        member_name = "John Doe" if i % 2 == 0 else "Jane Smith"
        claim_type = random.choice(claim_types_pool)
        diagnosis = random.choice(diagnoses_pool)
        submitted_amount = str(random.randint(1000, 15000))
        currency = "THB" if i % 2 == 0 else "VND" # Chia đều 50/50 tiền tệ gốc ban đầu
        submitted_date = "2024-03-15"
        status = random.choice(statuses_pool)
        
        # 2. Gài bẫy dữ liệu lỗi với tỷ lệ ~18% trên tổng số dòng độc nhất
        # Chia đều cơ hội xuất hiện cho các loại lỗi ở các cột
        if random.random() < 0.18:
            error_type = random.randint(1, 7)
            
            if error_type == 1:  # Khuyết mã định danh (Missing ID)
                if random.random() > 0.5: claim_id = ""
                else: policy_id = ""
                
            elif error_type == 2:  # Lỗi chữ hoa chữ thường (Inconsistent casing)
                member_name = random.choice(["john doe", "JOHN DOE", "jane smith", "JANE SMITH"])
                
            elif error_type == 3:  # Sai lỗi chính tả/viết tắt của loại quyền lợi (Claim Type Typos)
                claim_type = random.choice(["outpatient", "Outpateint", "OP", "inpatient", "dental"])
                
            elif error_type == 4:  # Diagnosis trống hoặc ký tự lạ (Missing/Null Marker)
                diagnosis = random.choice(["", "N/A", "n/a"])
                
            elif error_type == 5:  # Số tiền không hợp lệ (Invalid amounts)
                submitted_amount = random.choice(["-500", "0", "15,000", "8,500"])
                
            elif error_type == 6:  # Sai chuẩn currency (Phân bổ ĐỀU các lỗi thb, Baht, vnd)
                currency = random.choice(["thb", "Baht", "vnd"])
                
            elif error_type == 7:  # Loạn định dạng ngày tháng (Non-ISO dates)
                submitted_date = random.choice(["15/03/2024", "March 15, 2024", "2024.03.15"])
                
        rows.append([claim_id, policy_id, member_name, claim_type, diagnosis, submitted_amount, currency, submitted_date, status])
    
    # 3. Tiến hành bốc ngẫu nhiên các dòng đã tạo để nhân bản (Exact Duplicates)
    # Cộng thêm số dòng này vào thì tổng danh sách sẽ đạt CHÍNH XÁC 500 dòng
    for _ in range(exact_duplicates_count):
        rows.append(random.choice(rows).copy())
        
    # Xáo trộn lại danh sách một chút cho các dòng trùng lặp nằm rải rác thực tế hơn
    random.shuffle(rows)
        
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"[System] Successfully generated raw dirty dataset: {filename}")
    print(f" -> Total rows in file (including Header): {len(rows) + 1} rows.")
    print(f" -> Actual data rows: {len(rows)} rows.")

if __name__ == "__main__":
    generate_dirty_dataset()
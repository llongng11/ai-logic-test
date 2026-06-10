import csv
from datetime import datetime

def parse_dirty_date(date_str):
    """Hàm thông minh tự động nhận diện các kiểu định dạng ngày để đưa về ISO 8601 (YYYY-MM-DD)"""
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%B %d, %Y", "%Y.%m.%d"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return "INVALID_DATE"

def clean_and_report_claims(input_file="claims_dirty.csv", output_file="claims_clean.csv"):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            raw_rows = list(reader)
    except FileNotFoundError:
        print(f"[Lỗi] Không tìm thấy file {input_file}! Vui lòng chạy file 'generate_dirty_data.py' trước.")
        return
        
    total_rows_before = len(raw_rows)
    
    # Bộ đếm ghi nhận CHÍNH XÁC số lượng từng loại lỗi dựa trên file thô ban đầu
    issue_counts = {
        "Missing claim_id or policy_id": 0,
        "Inconsistent casing in member_name": 0,
        "Typos or non-standard claim_type": 0,
        "Missing or N/A diagnosis": 0,
        "Invalid submitted_amount (Negative, Zero, or String format)": 0,
        "Non-standard currency code": 0,
        "Non-ISO submitted_date format fixed": 0
    }
    
    # -------------------------------------------------------------------------
    # BƯỚC 1: QUÉT VÀ ĐẾM TOÀN BỘ LỖI TRÊN FILE THÔ
    # -------------------------------------------------------------------------
    for row in raw_rows:
        claim_id, policy_id, member_name, claim_type, diagnosis, submitted_amount, currency, submitted_date, status = row
        
        if not claim_id.strip() or not policy_id.strip():
            issue_counts["Missing claim_id or policy_id"] += 1
            
        if member_name != member_name.title():
            issue_counts["Inconsistent casing in member_name"] += 1
            
        claim_type_upper = claim_type.upper().strip()
        if claim_type_upper not in ["OUTPATIENT", "INPATIENT", "DENTAL"]:
            issue_counts["Typos or non-standard claim_type"] += 1
            
        if diagnosis.strip().lower() in ["", "n/a", "null"]:
            issue_counts["Missing or N/A diagnosis"] += 1
            
        try:
            amt_cleaned_str = submitted_amount.replace(",", "").strip()
            clean_amount = float(amt_cleaned_str)
            if clean_amount <= 0 or "," in submitted_amount or float(amt_cleaned_str) != int(float(amt_cleaned_str)):
                issue_counts["Invalid submitted_amount (Negative, Zero, or String format)"] += 1
        except ValueError:
            issue_counts["Invalid submitted_amount (Negative, Zero, or String format)"] += 1
            
        if currency.upper().strip() != currency or currency.upper().strip() == "BAHT":
            issue_counts["Non-standard currency code"] += 1
            
        if parse_dirty_date(submitted_date) == "INVALID_DATE" or parse_dirty_date(submitted_date) != submitted_date:
            issue_counts["Non-ISO submitted_date format fixed"] += 1


    # -------------------------------------------------------------------------
    # BƯỚC 2: CHUẨN HÓA DỮ LIỆU (NORMALIZE)
    # -------------------------------------------------------------------------
    normalized_rows = []
    
    for row in raw_rows:
        claim_id, policy_id, member_name, claim_type, diagnosis, submitted_amount, currency, submitted_date, status = row
        
        # Loại bỏ các dòng hỏng khóa chính nặng hoặc lỗi số tiền không thể xử lý tài chính
        if not claim_id.strip() or not policy_id.strip():
            continue  
            
        try:
            amt_cleaned_str = submitted_amount.replace(",", "").strip()
            clean_amount = float(amt_cleaned_str)
            if clean_amount <= 0:
                continue  # Hủy dòng tiền âm/bằng không
        except ValueError:
            continue  
            
        # Chuẩn hóa Tên KH
        member_name = member_name.title()
        
        # Chuẩn hóa Claim Type
        claim_type_upper = claim_type.upper().strip()
        if claim_type_upper in ["OUTPATIENT", "OP", "OUTPATEINT"]: norm_type = "OUTPATIENT"
        elif claim_type_upper == "INPATIENT": norm_type = "INPATIENT"
        elif claim_type_upper == "DENTAL": norm_type = "DENTAL"
        else: norm_type = "UNKNOWN"
            
        # Chuẩn hóa Diagnosis Null Marker
        diagnosis_clean = diagnosis.strip()
        if diagnosis_clean.lower() in ["", "n/a", "null"]:
            diagnosis_clean = "NOT_AVAILABLE"  
            
        # Chuẩn hóa Currency
        currency_upper = currency.upper().strip()
        if currency_upper == "BAHT": currency_upper = "THB"
            
        # Chuẩn hóa Ngày tháng
        clean_date = parse_dirty_date(submitted_date)
        if clean_date == "INVALID_DATE":
            # Lấy ngày hôm nay và định dạng ngay về chuỗi chuẩn YYYY-MM-DD
            clean_date = datetime.today().strftime("%Y-%m-%d")

        normalized_rows.append((claim_id, policy_id, member_name, norm_type, diagnosis_clean, int(clean_amount), currency_upper, clean_date, status))


    # -------------------------------------------------------------------------
    # BƯỚC 3: XÓA TRÙNG TUYỆT ĐỐI SAU CHUẨN HÓA & TÍNH THỐNG KÊ
    # -------------------------------------------------------------------------
    clean_rows = []
    seen_rows = set()
    duplicates_removed = 0
    
    stats_by_type = {}
    stats_by_status = {}
    diagnosis_counter = {}
    
    for row_tuple in normalized_rows:
        # Lúc này 'John Doe' và 'John DOE' đã đồng nhất cấu trúc, cam đoan bắt sạch trùng lặp ẩn
        if row_tuple in seen_rows:
            duplicates_removed += 1  
        else:
            seen_rows.add(row_tuple)
            clean_rows.append(list(row_tuple))
            
            # Tính toán số liệu thống kê Summary Statistics trên tập dữ liệu tinh khiết
            _, _, _, norm_type, diagnosis_clean, clean_amount, currency_upper, clean_date, status = row_tuple
            
            if norm_type not in stats_by_type: 
                stats_by_type[norm_type] = {"count": 0, "total_amt": 0.0}
            stats_by_type[norm_type]["count"] += 1
            stats_by_type[norm_type]["total_amt"] += clean_amount
            
            stats_by_status[status] = stats_by_status.get(status, 0) + 1
            
            if diagnosis_clean != "NOT_AVAILABLE":
                diagnosis_counter[diagnosis_clean] = diagnosis_counter.get(diagnosis_clean, 0) + 1

    # Xuất kết quả cuối cùng ra file CSV sạch
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(clean_rows)
        
    total_rows_after = len(clean_rows)
    top_5_diagnoses = sorted(diagnosis_counter.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # =========================================================================
    # TỪ ĐIỂN VIỆT HOÁ THÔNG TIN LỖI
    # =========================================================================
    vietnamese_issues = {
        "Missing claim_id or policy_id": "Thiếu mã claim_id hoặc policy_id",
        "Inconsistent casing in member_name": "Tên thành viên viết hoa thường lộn xộn",
        "Typos or non-standard claim_type": "Sai chính tả / sai định dạng loại hình khám",
        "Missing or N/A diagnosis": "Thiếu thông tin chẩn đoán bệnh",
        "Invalid submitted_amount (Negative, Zero, or String format)": "Số tiền không hợp lệ (âm, bằng 0 hoặc sai kiểu chuỗi)",
        "Non-standard currency code": "Sai mã tiền tệ (không viết hoa hoặc dùng chữ BAHT)",
        "Non-ISO submitted_date format fixed": "Sai định dạng ngày tháng (đã chuẩn hóa về ISO)"
    }

    vietnamese_status = {
        "APPROVED": "ĐÃ DUYỆT (APPROVED)",
        "REJECTED": "TỪ CHỐI (REJECTED)",
        "PENDING": "ĐANG XỬ LÝ (PENDING)",
        "IN_REVIEW": "ĐANG XEM XÉT (IN_REVIEW)"
    }

    vietnamese_types = {
        "OUTPATIENT": "NGOẠI TRÚ (OUTPATIENT)",
        "INPATIENT": "NỘI TRÚ (INPATIENT)",
        "DENTAL": "NHA KHOA (DENTAL)",
        "UNKNOWN": "CHƯA XÁC ĐỊNH (UNKNOWN)"
    }

    # =========================================================================
    # IN BÁO CÁO CHẤT LƯỢNG DỮ LIỆU
    # =========================================================================
    print("\n" + "="*65)
    print("               BÁO CÁO CHẤT LƯỢNG DỮ LIỆU BỒI THƯỜNG")
    print("="*65)
    print(f"Tổng số dòng ban đầu          : {total_rows_before}")
    print(f"Tổng số dòng sau khi xử lý    : {total_rows_after}")
    print(f"Số dòng trùng lặp đã loại bỏ  : {duplicates_removed}")
    print("-"*65)
    print("THỐNG KÊ CÁC LỖI DỮ LIỆU PHÁT HIỆN:")
    for issue_name, count in issue_counts.items():
        vn_issue = vietnamese_issues.get(issue_name, issue_name)
        print(f" • {vn_issue}: {count} dòng")
    print("-"*65)
    print("THỐNG KÊ THEO LOẠI HÌNH KHÁM (SỐ CA & SỐ TIỀN TRUNG BÌNH):")
    for c_type, data in stats_by_type.items():
        avg_amount = data["total_amt"] / data["count"]
        vn_type = vietnamese_types.get(c_type, c_type)
        print(f" • {vn_type}: Số ca = {data['count']}, Trung bình = {avg_amount:,.2f} THB")
    print("-"*65)
    print("THỐNG KÊ THEO TRẠNG THÁI HỒ SƠ:")
    for stat, count in stats_by_status.items():
        vn_status = vietnamese_status.get(stat, stat)
        print(f" • {vn_status}: {count} ca")
    print("-"*65)
    print("TOP 5 CHẨN ĐOÁN BỆNH PHỔ BIẾN NHẤT:")
    for idx, (diag, count) in enumerate(top_5_diagnoses, 1):
        print(f"  {idx}. {diag}: {count} ca")
    print("="*65 + "\n")

if __name__ == "__main__":
    clean_and_report_claims()
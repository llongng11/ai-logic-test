# AI Challenge 02 — Claims Data Cleanup & Report

## Làm rõ yêu cầu:

Với thử thách này, tôi xác định bài toán chính cần giải quyết là xây dựng một module chuẩn hoá dữ liệu nhằm xử lý và làm sạch một file .csv thô chứa nhiều lỗi cấu trúc (lỗi có thể xuất phát từ con người như nhập tay sai định dạng, viết sai chính tả, hoặc bấm gửi nhiều lần gây ra dữ liệu trùng lặp), đồng thời xuất ra một báo cáo chi tiết về số lượng từng loại lỗi phát hiện và các số liệu thống kê tổng hợp (Summary Statistics) sau khi làm sạch.

## Ước lượng thời gian thực hiện:

Tổng thời gian hoàn thành: ~3 giờ

- 30 phút: Đọc hiểu yêu cầu nghiệp vụ, phân rã các loại lỗi dữ liệu và xây dựng các tầng xử lý cho thuật toán chuẩn hoá.
- 60 phút: Viết file sinh dữ liệu ngẫu nhiên, điều hướng AI (Gemini) để hỗ trợ việc sinh dữ liệu có độ bao phủ hết các lỗi và sự phân bổ các trường hợp lỗi đồng đều.
- 90 phút: Chạy thực tế, kiểm thử, đối chiếu số liệu và viết tài liệu này.

## Phân tích dữ liệu thô (Dirty Dataset):

Để đảm bảo có một tập dữ liệu đủ thử thách đúng nghĩa cho việc kiểm thử, tôi cùng với sự hỗ trợ của Gemini đã thiết kế một module có thể tái sử dụng và sinh ra dữ liệu ngẫu nhiên ở mỗi lần chạy, nằm trong file generate_dirty_data.py. Module này tuân thủ các quy tắc phân bổ dữ liệu như sau:

- Quy mô dữ liệu thô luôn đạt chính xác 500 dòng (bao gồm cả dòng lỗi và dòng trùng lặp), và 01 dòng cho header.
- Phân bổ lỗi đồng đều theo quy tắc sau:
  - Đầu tiên, thực hiện sinh 490 dòng dữ liệu, gài bẫy lỗi với tỉ lệ 18% (theo khung đề bài yêu cầu). Khi một dòng được xác định là dòng lỗi, thuật toán sẽ sử dụng hàm phân phối đều random.randint(1, 7) để chia đều cơ hội xuất hiện cho 7 loại lỗi khác nhau trên các cột, cụ thể là:
    1. Missing ID (claim_id / policy_id): Khuyết mã định danh.
    2. Inconsistent casing (member_name): Tên khách hàng được viết hoa, thường không đồng nhất theo chuẩn (john doe, JOHN DOE, JANE SMITH).
    3. Claim Type Typos (claim_type): Sai chính tả hoặc viết tắt loại hình khám (Outpateint, OP, outpatient).
    4. Null Marker (diagnosis): Cột chẩn đoán bị trống hoặc dính ký tự rác không đồng nhất ("", N/A, n/a).
    5. Invalid Amount (submitted_amount): Số tiền không hợp lệ (tiền âm -500, bằng 0, hoặc dính dấu phẩy định dạng chuỗi "15,000").
    6. Mixed Currency (currency): Mã tiền tệ không đồng nhất, sai chuẩn ISO (viết thường thb, vnd hoặc ghi chữ Baht).
    7. Non-ISO Date (submitted_date): Định dạng ngày tháng không đồng nhất, sai chuẩn ISO (15/03/2024, March 15, 2024, 2024.03.15).

  - Sau đó, trong 490 dòng dữ liệu đã sinh ra, tiến hành chọn ra 10 dòng để nhân bản.
  - Xáo trộn lại danh sách để các dòng phân bổ tự nhiên hơn.

## Phân tích và xây dựng thuật toán chuẩn hoá:

- Trong giai đoạn chuẩn hoá này, tôi chia làm 3 bài toán tách bạch và cần được giải quyết theo thứ tự như sau:

1.  Trong tập dữ liệu thô ban đầu, phải đếm và thống kê được tất cả lỗi dữ liệu có thể phát hiện.
2.  Thực hiện chuẩn hoá dữ liệu, những dòng lỗi sẽ được chuẩn hoá và giữ lại, hoặc loại bỏ tuỳ theo loại lỗi.
3.  Dựa trên tập dữ liệu mới sau khi được chuẩn hoá ở bước 2:
    - Những dòng được phát hiện trùng lặp sẽ được loại bỏ theo quy tắc giữ dòng trước, bỏ dòng sau.
    - Những dòng còn lại sẽ được áp dụng để thực hiện các thống kê theo loại hình khám, thống kê theo trạng thái hồ sơ, top 5 chấn đoán bệnh phổ biến nhất.

- Vì sao sau khi chuẩn hoá dữ liệu mới tiến hành xoá bỏ những dòng trùng lặp?
  - Vì tồn tại một bài toán "trùng lặp ẩn", lấy ví dụ có hai giá trị chuỗi là "a" và "A". Trước khi chuẩn hoá, ta mặc định xem hai giá trị này là "không trùng lặp". Tuy nhiên sau khi chuẩn hoá về một chuẩn nào đó, hai giá trị chuỗi này sẽ giống nhau, lúc này sự trùng lặp mới xuất hiện.
  - Để giải quyết bài toán này, thuật toán cần đảm bảo đưa hết các dòng dữ liệu về cùng 1 chuẩn, rồi mới tiến hành phát hiện và loại bỏ những dòng trùng lặp.

## Giải thích mã nguồn (file data_processor.py):

1.  Bước 1: Quét và đếm
    Thực hiện kiểm tra toàn bộ các lỗi theo cấu trúc đã xác định ở phần "Phân tích dữ liệu thô" và ghi nhận vào biến đếm issue_counts.

2.  Bước 2: Chuẩn hoá, thực hiện lặp qua các dòng như sau:
    - Loại bỏ những dòng thiếu khoá chính (claim_id hoặc policy_id).
    - Sử dụng khối try-except để loại bỏ những dòng có số tiền (submitted_amount) âm hoặc bằng 0.
    - Chuẩn hoá tên khách hàng bằng hàm .title().
    - Chuẩn hoá loại hình khám (claim_type) về cùng định dạng như OUTPATIENT, INPATIENT, DENTAL và UNKNOWN.
    - Chuẩn hoá chuỗi ký tự trống của cột chẩn đoán (diagnosis) về "NOT_AVAILABLE".
    - Chuẩn hoá đơn vị tiền tệ (currency): Đưa tất cả về dạng đơn vị chuẩn ISO như THB, VND.
    - Chuẩn hoá ngày tháng (submitted_date): Đưa tất cả về cùng định dạng yyyy-mm-dd, nếu là chuỗi lỗi thì trả về ngày hiện tại.

3.  Bước 3: Khử trùng lặp và tích luỹ số liệu thống kê:
    - Sử dụng biến nhớ seen-rows dưới dạng cấu trúc set() để tối ưu tốc độ.
    - Cơ chế hoạt động: Khi duyệt qua 1 dòng (row_tuple), thực kiện kiểm tra dòng này đã xuất hiện trong seen_rows hay chưa.
      - Nếu đã xuất hiện: Tăng biến đếm duplicates_removed lên 1 và bỏ qua dòng này.
      - Nếu chưa xuất hiện: Ghi nhận dòng này vào seen_rows, đồng thời thêm dòng đó vào tập dữ liệu "sạch" clean_rows, từ clean_rows ta phân rã các giá trị norm_type, diagnosis_clean, clean_amount và status để thực hiện các thống kê sau:
        - Thống kê theo loại hình khám (stats_by_type): Gom nhóm và cộng dồn đồng thời cả count (số ca) lẫn total_amt (tổng tiền) của từng loại INPATIENT, OUTPATIENT, DENTAL.
        - Thống kê theo trạng thái (stats_by_status): Dùng hàm .get(status, 0) + 1 để đếm nhanh số lượng hồ sơ theo từng trạng thái APPROVED, REJECTED,...
        - Tìm Top 5 bệnh phổ biến (diagnosis_counter): Loại bỏ nhãn NOT_AVAILABLE (những ca bị khuyết bệnh nền đã xử lý ở Bước 2) để bảng xếp hạng bệnh tật không bị dính ký tự rác.

4.  Bước 4: Việt hoá thông tin và xuất file
    - Sử dụng các biến từ điển vietnamese_issues, vietnamese_status và vietnamese_types để ánh xạ toàn bộ thuật ngữ sang tiếng Việt và in ra màn hình Terminal
    - Sử dụng bộ nhớ clean_rows để xuất ra các dòng dữ liệu cho file kết quả claims_clean.csv.

## Hướng dẫn sử dụng

1.  Bước 1: Sinh file dữ liệu thô

    > python generate_dirty_data.py

2.  Bước 2: Chuẩn hoá dữ liệu và xuất báo cáo

    > python data_processor.py

## Công nghệ sử dụng

- Ngôn ngữ: Python 3.12 (thư viện csv, datetime, random)
- Công cụ AI: Gemini (điều hướng phát triển), Github Copilot (Hỗ trợ sinh comment, correct syntax)

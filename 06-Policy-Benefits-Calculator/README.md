# AI Challenge 06 — Policy Benefits Calculator

## Làm rõ yêu cầu:

Bài toán cốt lõi của thử thách này là xây dựng một module tính toán quyền lợi bảo hiểm. Module này đóng vai trò như một dịch vụ tự động: Nhận đầu vào là cấu hình điều khoản gói bảo hiểm (JSON) và danh sách chi phí y tế thô của khách hàng, sau đó bóc tách, áp dụng dồn tích các quy tắc nghiệp vụ bảo hiểm theo đúng trục thời gian tuyến tính để đưa ra kết quả phân bổ chi phí chính xác (Bảo hiểm trả bao nhiêu, Khách tự trả bao nhiêu, Lý do vì sao).

## Ước lượng thời gian thực hiện:

Tổng thời gian hoàn thành: ~5 giờ

- 60 phút: Nghiên cứu nghiệp vụ bảo hiểm (Hạn mức năm, hạn mức lần khám, đồng chi trả, khấu trừ đầu kỳ, thời gian chờ) và thiết kế luồng đi của dòng tiền.
- 30 phút: Thiết kế bộ dữ liệu đầu vào gồm file cấu hình policy.json và tệp 20 hồ sơ expenses.json sao cho bao phủ toàn bộ các bẫy logic của đề bài.
- 120 phút: Viết mã nguồn module calculator.py theo kiến trúc phân tầng bộ lọc (cửa chặn).
- 90 phút: Viết bộ 10 Unit Tests kiểm thử tự động, chạy thực tế và viết tài liệu này.

## Thiết kế dữ liệu đầu vào:

Để thuật toán được thử nghiệm toàn diện nhất, tôi cùng với sự hỗ trợ của Gemini đã thiết kế một cặp dữ liệu bổ trợ cho nhau:

- Cấu hình gói bảo hiểm (policy.json):
  - Thiết lập quỹ cố định ở mức 100.000THB.
  - Áp dụng mức khấu trừ đầu năm (Đeuctible) là 1000 THB.
  - Quy định thời gian chờ (Waiting Period) tăng dần tuỳ theo mức độ nặng nhẹ của nhóm quyền lợi thăm khám (Nội trú chờ 30 ngày, Nha Khoa chờ 90 ngày) kèm danh mục bệnh loại trừ tuyệt đối (exclusions)

- Danh sách 20 chi phí y tế (expenses.json):
  - Được sắp xếp rải đều từ tháng 1 đến tháng 12 năm 2024 để ép hệ thống phải xử lý dồn tích theo thời gian.
  - Các hồ sơ này chứa đầy đủ các kịch bản: đi khám quá sớm khi chưa hết thời gian chờ (EXP-003 bị từ chối), dính bệnh cấm (EXP-005), đắp tiền cho đủ mức khấu trừ đầu kỳ (EXP-001, EXP-002), chạm trần giới hạn lần khám, chia tỷ lệ đồng chi trả 80/20, và các ca cuối năm làm cạn sạch quỹ tiền 100,000 THB của hợp đồng.

## Kiến trúc thuật toán 6 tầng

Đối với mỗi hồ sơ chi phí y tế, để tính ra được số tiền bảo hiểm chi trả chính xác đến từng đồng, tôi xây dựng thuật toán theo mô hình thác đổ, bắt buộc số tiền hóa đơn gốc phải đi qua lần lượt 6 tầng kiểm tra sau:

- Tầng 1 - Kiểm tra Danh mục loại trừ & Thời gian chờ: Đây là cửa chặn hành chính nhằm kiểm tra xem bệnh nền có bị cấm tuyệt đối (như phẫu thuật thẩm mỹ) hoặc khách đi khám quá sớm khi chưa hết thời gian chờ của gói hay không; nếu dính bẫy, hồ sơ bị từ chối.
- Tầng 2 - Kiểm tra Quỹ năm còn lại: Hệ thống kiểm tra dung lượng ví tiền tổng của cả năm. Nếu quỹ này đã cạn kiệt về mức 0 từ các ca trước, hệ thống lập tức khóa sổ và từ chối chi trả.
- Tầng 3 - Áp dụng mức Khấu trừ (Deductible): Hóa đơn sẽ bị trích một phần hoặc toàn bộ số tiền để tích lũy cho đủ chỉ tiêu khách phải tự trả đầu năm; nếu số tiền này nuốt trọn hóa đơn, quy trình dừng lại và khách phải tự chi trả 100% chi phí.
- Tầng 4 - Áp trần Giới hạn mỗi lần khám (Per-Visit Limit): Hệ thống lấy số tiền còn lại sau khấu trừ để so khớp với trần chi trả của một lần đi khám. Nếu số tiền vượt quá hạn mức nhóm quyền lợi đó, thuật toán sẽ chủ động "cắt ngọn" phần thừa để đưa về đúng mức trần cho phép.
- Tầng 5 - Chia tỷ lệ Đồng chi trả (Co-payment %): Số tiền hợp lệ trong trần sẽ được mang đi chia theo tỷ lệ cấu hình của gói (ví dụ bảo hiểm trả 80%, khách trả 20%) để bóc tách ra số tiền bảo hiểm định chi và số tiền khách phải tự trả tiền túi.
- Tầng 6 - Cắt ngọn theo Quỹ năm thực tế: Số tiền bảo hiểm định chi ở Tầng 5 sẽ được đối chiếu với số dư thực tế của quỹ năm. Nếu quỹ năm còn quá ít không đủ trả, hệ thống sẽ thực hiện quyền cắt giảm, chỉ chi trả phần dung lượng cuối cùng đó và bắt buộc khách trả phần hụt còn lại trước khi chốt số liệu.

## Giải thích mã nguồn (file calculator.py):

Mã nguồn được viết theo kiến trúc hướng đối tượng (OOP), giữ trạng thái biến thiên của hợp đồng thông qua các thuộc tính của class PolicyBenefitsCalculator như self.remaining_annual_limit và self.accumulated_deductible.

1. Xử lý dồn tích theo thời gian (process_expenses): Thuật toán không xử lý bừa bãi mà việc đầu tiên là dùng lệnh sorted(expenses, key=lambda x: x["date"]) để sắp xếp lịch các hồ sơ theo thứ tự từ trước đến nay. Ca nào nộp trước ăn vào hạn mức trước, ca sau chịu ảnh hưởng của ca trước.

2. Quản lý lý do chi trả chặt chẽ: Khởi tạo một Object kết quả với reason_id mặc định. Tùy thuộc vào việc dòng tiền bị chặn lại hoặc rẽ nhánh ở cửa nào, hệ thống sẽ gán đúng mã reason_id của cửa đó (ví dụ: WAITING_PERIOD_DENIED, DEDUCTIBLE_ABSORBED, COPAY_APPLIED, ANNUAL_LIMIT_CAPPED). Điều này giúp hệ thống Core Bảo hiểm dễ mapping, tra cứu log và xuất báo cáo tự động mà không sợ bị sai lệch chuỗi ký tự text do khác biệt ngôn ngữ hay khác biệt về case.

3. Tối ưu kiểu dữ liệu: Toàn bộ số tiền sau khi nhân chia tỷ lệ phần trăm (float) đều được ép kiểu về số nguyên int() ở đầu ra cuối cùng, đảm bảo tệp JSON xuất ra sạch sẽ, không bị dính các lỗi hiển thị kiểu số thập phân vô tận (như 500.0000000001).

## Chiến lược kiểm thử tự động (file test_calculator.py):

Bộ Unit Test gồm 10 bài test độc lập được xây dựng bằng thư viện unittest nhằm kiểm tra độ bền bỉ của thuật toán thông qua việc cô lập và giả lập dữ liệu:

- Test 1, 2, 3, 8: Kiểm thử các điều kiện biên cứng như nuốt trọn hóa đơn vào khấu trừ, từ chối do nằm viện trong thời gian chờ, từ chối bệnh loại trừ, và phát hiện quyền lợi lạ (VISION) không có trong hợp đồng.
- Test 4, 5: Kiểm tra tính chính xác của toán học khi vừa dính trần lần khám, vừa phải chia tỷ lệ đồng chi trả 80/20.
- Test 6, 7: Giả lập trạng thái ví năm cạn kiệt hoàn toàn hoặc còn dung lượng cực ít (remaining_annual_limit = 500) xem thuật toán có cắt gọt phần bảo hiểm chi trả chuẩn xác hay không.
- Test 9: Thử thách chuỗi khấu trừ liên tiếp (Hóa đơn 1 ăn một phần, hóa đơn 2 ăn nốt phần còn lại rồi mới kích hoạt bảo hiểm) để chứng minh bộ nhớ dồn tích hoạt động hoàn hảo.
- Test 10: Đảm bảo quyền lợi Nội trú (Copay 0%) được chi trả trọn gói 100% không khấu hao.

## Hướng dẫn sử dụng:

1.  Bước 1: Chạy file main.py để xem nhật ký và báo cáo tổng kết quyền lợi đến cuối năm.

    > python main.py

2.  Bước 2: Chạy unit test để kiểm tra thuật toán có hoạt động ổn định không.

    > python test_calculator.py

Lưu ý: Người đánh giá bài test có thể thay đổi nội dung của file policy.json hay expenses.json để test theo mẫu dữ liệu tuỳ ý khác.

## Công nghệ sử dụng

- Ngôn ngữ: Python 3.12 (thư viện json, datetime, unittest)
- Công cụ AI: Gemini (điều hướng phát triển), Github Copilot (Hỗ trợ sinh comment, correct syntax)

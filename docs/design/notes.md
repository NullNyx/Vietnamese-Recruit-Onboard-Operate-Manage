# Design Notes

## Inbox

- Inbox là intake surface, không phải All Work.
- Dữ liệu vào còn thô: email, request, file, notification, system signal.
- Mục tiêu chính: triage nhanh, nối context, chuyển thành work item, hoặc dismiss.

## Layout grammar

- Shell giữ nguyên: sidebar trái + main area.
- Header gồm eyebrow, title, brief copy.
- Main ưu tiên list + triage actions + filter row.
- Empty/loading/error phải có mặt trong mỗi screen family.

## Tone và hệ thống

- AI Labs: nền paper white, 1 accent green duy nhất, flat, quiet.
- Font: IBM Plex Sans cho nội dung, IBM Plex Mono cho label/eyebrow.
- Không gradient, không bokeh, không decor dư, không marketing layout.

## Inbox-specific rules

- Item phải cho thấy title, source, requester/owner nếu có, age/received time, triage status, priority/risk hint nếu có.
- Action chính là triage/classify, link context, mark as work item, dismiss, assign, open detail.
- Batch action bằng checkbox chỉ để tăng tốc intake.
- Khác All Work ở chỗ Inbox xử lý raw intake, chưa sạch thành queue chuẩn.

## Documents

- Documents là context library thứ cấp, không phải file manager chung.
- Entry point chỉ từ Work Detail hoặc shell Search; màn này dùng để tra giấy tờ khi cần ngữ cảnh.
- Default ưu tiên list view; detail chỉ để inspect metadata, preview, linked people, related contracts, audit.
- Empty state phải nhắc rõ nơi mở đúng: shell Search hoặc Work Detail.
- Loading state giữ shell và skeleton list để không phá nhịp IA.

## Search

- Search là shell-level pattern, không phải screen độc lập.
- Search mở từ toolbar / overlay / drawer, trả kết quả cross-library.
- Search design nằm ở `docs/design/components/search.lib.pen`.
- Search chỉ là đường vào context; sau chọn kết quả thì quay về surface gốc.

## Lưu ý quan trọng khi sửa `.pen`

- Không dùng Python script để đọc-sửa-ghi `.pen`.
- `.pen` phải sửa qua Pencil MCP, rồi kiểm trong editor active.
- Không tự ý đổi ref ID giữa file nếu chưa biết Pencil resolve workspace thế nào.
- Không đụng `themes`, `variables`, `fileToken` bằng script thô.
- Không nhân rộng sửa hàng loạt trước khi verify 1 file trong Pencil.
- Nếu cần điều tra cấu trúc, chỉ đọc thô hoặc dùng Pencil MCP read-only.

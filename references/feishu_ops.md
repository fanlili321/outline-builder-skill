# 飞书文档操作命令手册（大纲配图用）

全部经458期实测（2026-07）。调用前：
```bash
export PATH="/Users/fanlili/.npm-global/bin:$PATH" LARK_CLI_NO_PROXY=1
```
doc_token 从链接 `/docx/XXXX` 取。lark-cli 的 `-o`/`--file` 只接受**当前目录下的相对路径**，先 cd 到工作目录。

## 读文档全文
```bash
lark-cli api GET /open-apis/docx/v1/documents/{doc_token}/raw_content --jq '.data.content'
```

## 读批注（找 @AI 任务）
```bash
lark-cli api GET "/open-apis/drive/v1/files/{doc_token}/comments" \
  --params '{"file_type":"docx","page_size":100}' \
  --jq '[.data.items[] | {quote, solved: .is_solved, replies: [.reply_list.replies[].content.elements[].text_run.text], images: [.reply_list.replies[].extra.image_list // [] | .[]]}]'
```
- `quote` = 被批注的原句 → 后面 media-insert 的锚点
- replies 里含 `@AI` 的才是出图任务；其他批注是给钉大的说明，出图时要遵守其中的口径要求
- `images` 是批注附图 token（样式参考图），用下面的下载命令取来看

## 下载附件/图片（xlsx、批注参考图）
```bash
cd 工作目录 && lark-cli api GET /open-apis/drive/v1/medias/{file_token}/download -o ./本地名
```
附件 token 在 blocks 里找：block_type=23 的 `file.token`（文件名在 `file.name`），图片是 block_type=27 的 `image.token`。

## 拉块结构（找锚点/附件/核验插图）
```bash
lark-cli api GET /open-apis/docx/v1/documents/{doc_token}/blocks --params '{"page_size":500}' --page-all
```
根块 block_id=doc_token，其 `children` 数组即顶层顺序。文本块 block_type=2，图片27，附件23，grid列25（用户手动并排图片时图会挂在grid列下，不在根children里——删/查图先确认实际parent）。

## 插图（核心命令，一步到位）
```bash
lark-cli docs +media-insert --doc {doc_token} --file ./图.png \
  --selection-with-ellipsis "锚点原句或唯一前缀" \
  --caption "图片来自AI，仅供示意，ppt中会重新作图，并核对数据"
```
- 插在匹配文字块正下方；锚点文字不唯一时用 `"前缀...后缀"` 消歧
- 同一锚点插多张：**后插的在前**（要 A,B 顺序就先插 B 再插 A）
- 锚点在 callout/表格里时图会插到容器外

## 改图片说明文字（不删图）
```bash
lark-cli api PATCH /open-apis/docx/v1/documents/{doc}/blocks/{img_block_id} \
  --data '{"replace_image":{"token":"原图token","caption":{"content":"新说明"}}}'
```
原图token从 blocks 里该图片块的 `image.token` 取。caption 渲染为图片下方灰色小字。

## 删块（删旧图）
```bash
lark-cli api DELETE /open-apis/docx/v1/documents/{doc}/blocks/{parent_id}/children/batch_delete \
  --data '{"start_index":i,"end_index":i+1}'
```
index 从 parent 的 children 数组里查；**每删一次都要重新拉 blocks 刷新索引**（索引会变）。

## 插图后核验（必做）
重新拉 blocks，对每张新图确认：(1) 在 parent children 里的位置紧跟锚点文字块；(2) `image.token` 非空（绑定成功）。

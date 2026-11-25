# 现用工具

接入新工具前先读 README、确认许可证，并在样片上跑通一条命令。换脸、deepfake、克隆爆款、去水印、搬运下载器不写入这张表。

| 环节 | 工具 | 用法 |
| --- | --- | --- |
| 切点、响度、接触表 | probe_reference.py | 复刻先测量参考片 |
| 导演本检查 | check_plan.py | 没过不许导出 |
| 按骨架出片 | assemble.py | 只吃用户自己的素材 |
| 成片裁判 | score_replica.py | 退出码 0 才是完成 |
| 口播精修、花字 | video-editing-skill | 读该技能后使用 |
| 纪录片组装 | video-editing | 读该技能后使用；导出后仍要打分 |
| 剪映工程、中文配音 | jianying-editor | 读该技能后使用；导出 mp4 再打分 |
| 字与图形成片 | openfilm | 没有实拍时用；渲染后打分 |
| 配乐与音效 | generate_audio | 只有器乐和音效，不生成歌词人声 |

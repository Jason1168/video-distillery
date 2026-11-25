---
name: film-craft-distill
description: >-
  Distills high-craft films on a daily global pass, scans GitHub for
  video-production tools, and rebuilds an original film from a reference
  until a measured 95-point craft gate passes. Eighty is only the restart
  floor, not a delivery score. Use when the user asks for 每天蒸馏, 全球扫片,
  参考片, 复刻, 仿拍, 对标成片, 导演, 编剧, a documentary or commercial
  finish, or a GitHub scan for video-editing tools. Also use when today's
  craft digest is missing or a reference cut needs to clear 95.
---

# 成片蒸馏与复刻

完成线是 **95**。80 分以下是废片，推倒节奏骨架重做。80 到 94 是半成品，只改最低的两项后再导出。没有 `score_replica.py` 的退出码 0，不能说完成，不能说 95。

复刻的是节奏、镜头功能、声音和完成度。故事、人物、台词、人脸、原片画面都是新的。`assemble.py` 不接受参考片路径。

## 先选路

用户要复刻时，直接做复刻，不要先写今天的远观卡片。

用户要「跑今天的蒸馏」，或今天的 `library/digests/日期.md` 不存在且对方要的就是扫描时，跑每天那条。做片子时如果今天的名单已经在，先看 `library/toolchain.md`，只在新工具明显强过表现有环节时才接入。

技能目录就是本文件所在目录。下面写成 `<SKILL_ROOT>`。

## 复刻

工作目录在用户项目里：`film-replica/<片名>/`。

1. 读 [references/director-writer.md](references/director-writer.md)，先判断类型：剧情短片、纪录片、视频论文、品牌片、MV。类型错了，节奏打满也过不了结构。
2. 测量参考片。长片不要整部一次打，按 8 到 12 分钟一盘，参考和成片用同一对 `--reel 开始 结束`。

```bash
python3 "<SKILL_ROOT>/scripts/probe_reference.py" "参考片.mp4" --out "film-replica/<片名>/reference"
```

3. 读完 `reference/sheets/` 里每一张接触表，再读切点静帧。切点超过 24 张时，至少读开头、每个结构转折、结尾，以及特别长或特别短的刀。没看过的画面不能写进镜头语法。
4. 填 `reference/skeleton.json`。每个槽位写 `function`、`picture`、`sound`。`picture` 必须是能拍到的动作和物件。有字就写 `text`。同时写 `screenplay.md`：控制思想、结尾要让人相信的一件事、开场 8 秒、转折的时间码和信息、不抄的三样。节拍引用槽位编号，不要另做一份镜头表。
5. 检查导演本。不过就改骨架，不要开始剪。

```bash
python3 "<SKILL_ROOT>/scripts/check_plan.py" --skeleton "film-replica/<片名>/reference/skeleton.json" --probe "film-replica/<片名>/reference/probe.json" --stage plan
```

6. 给每个槽位填用户自己的 `source` 和入点 `in`。素材不够长就换素材或改 picture，不要把参考片填进去。超过两成槽位写着待补，先改剧本。
7. 再查一次 `--stage assemble`。通过后按类型出片：

| 成片 | 做法 |
| --- | --- |
| 用户素材硬切，要锁时长和响度 | `assemble.py` |
| 口播、跳切、花字 | 先读 `video-editing-skill`，导出后仍要打分 |
| 多素材纪录片 | 先读 `video-editing`，导出后仍要打分；节奏不够就回到骨架重切 |
| 剪映特效、中文配音、平台成片 | 先读 `jianying-editor`，导出 mp4 再打分 |
| 没有实拍，靠字和图形成片 | 先读 `openfilm`，场景时长跟槽位走，渲染后打分 |
| 配乐、音效 | `generate_audio`，只要器乐和音效，不生成歌词人声 |

默认硬切：

```bash
python3 "<SKILL_ROOT>/scripts/assemble.py" \
  --skeleton "film-replica/<片名>/reference/skeleton.json" \
  --probe "film-replica/<片名>/reference/probe.json" \
  --out "film-replica/<片名>/output.mp4"
```

8. 测量成片，再打分。用 assemble 出的片，带上旁边的 `output.assemble-notes.json`。剪映或 OpenFilm 出的片，先看画面，写 `graphics-seen.json`：`{"inspected": true, "evidence": "0:03 底部白字在说这一场的转折"}`。

```bash
python3 "<SKILL_ROOT>/scripts/probe_reference.py" "film-replica/<片名>/output.mp4" --out "film-replica/<片名>/replica"
python3 "<SKILL_ROOT>/scripts/score_replica.py" \
  --reference "film-replica/<片名>/reference/probe.json" \
  --replica "film-replica/<片名>/replica/probe.json" \
  --craft "film-replica/<片名>/craft-scores.json" \
  --skeleton "film-replica/<片名>/reference/skeleton.json" \
  --notes "film-replica/<片名>/output.assemble-notes.json"
```

9. 按脚本印出的结论做。废片推倒重来。半成品只改它点名的两项。过线但还有一项是 8，再改一轮，然后停。同一版最多三轮。三轮后仍低于 95，报告分数、卡住的两项、缺的是素材、声音还是镜头语法。

分数怎么算，看 [references/quality-gate.md](references/quality-gate.md)。脚本和文档不一致时，以脚本为准。`python3 "<SKILL_ROOT>/scripts/score_replica.py" --self-test` 应通过。

交付时长如果本来就不是参考片时长，打分加 `--brief-duration 秒`。平均镜头长度仍然对参考片。

## 全片卡片

按 [references/craft-card.md](references/craft-card.md) 的「全片」写到 `film-replica/<片名>/craft-card.md`。`craft-scores.json` 的六个分数都要有时间码证据。`upgrade_dimension` 和骨架里的相同，而且这一项至少 9。全是 9 分、技术满分，总分是 94，仍然不能交付。

## 每天

本机 8:15 会跑收集。名单在 `library/digests/日期.md`。收集任务不会写导演判断。

```bash
python3 "<SKILL_ROOT>/scripts/daily.py"
```

「跑今天的蒸馏」时：

1. 名单不存在，或文件里是 `status: partial`，就跑上面的命令。`--force` 只在源坏了需要重抓时用。
2. 影片和视频论文里取最前面 3 条，打开公开链接，按「远观」模板写到 `library/craft/日期/`。只写页面上有的事实。没有画面就不要写景别、切点、调色。
3. 「可以评估」里最多看 3 个仓库的 README。接入、观望、拒绝写回名单。接入的条件：许可证清楚，能替换 `library/toolchain.md` 里的一个环节，并且在样片上跑通了一条命令。未标许可证只能观望。
4. 拒绝类（换脸、deepfake、克隆爆款、去水印、搬运下载器）不安装，不试跑。

加源只改 `library/sources.json`。字段：`name`、`tier`（`film`、`essay`、`craft-article`）、`kind`（`rss` 或 `youtube`）、`url`，可选 `link_contains`、`undated_keep`。

定时任务如果掉了，再跑一次 `bash "<SKILL_ROOT>/scripts/install_schedule.sh"`。

## 不能做的事

- 不下载、不重编码、不搬运用户没有权利的成片。每天的扫描只留公开链接和简介。
- 不把参考片的画面、人脸、表演或台词放进槽位。
- 不接入换脸和「克隆一条爆款」的仓库，哪怕它星很多。
- 远观卡片不伪装成看过片。测量不完整的探针不过 95。

# SV Investigator 字段词典

> 自动生成自 `architecture/data_lineage.json`；源指纹 `89e4ddcc1d99`。
> 请勿直接编辑本文件。

## 0. 用户输入

接收坐标、参考基因组、SVTYPE、断点不确定性、统计和质量信息。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| input.{genome_build,chrom,start,end,sv_type} | object | 候选身份的五个必填字段。 | 任一缺失即 validation_error。 |
| input.{CIPOS,CIEND,CIMATE,IMPRECISE} | object\|null | VCF 断点不确定性及不精确标志；[0,0] 表示零宽区间，不表示缺失。 | 省略或设为 null；下游仅用带标签的 ±500 bp fallback 检索附近候选。 |
| input.{ALT,mate_chrom,mate_pos,CHR2,END} | object\|null | BND mate 坐标与方向来源。 | BND 降级为 first-breakend-only。 |
| input.{sv_id,length_bp,statistics,quality,source_record} | object\|null | 上游标识、长度、统计、质量和原 VCF 记录。 | 保留显式 warning 或空对象。 |

处理规则：

- 此阶段只提供外部输入字段。

实现位置：`README.md / tools.py:normalize_sv_input`

## 1. 确定性标准化

统一 build、染色体与 SVTYPE，验证坐标，解析 CI 和 BND mate；工具直接把完整结果写入状态。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| normalized_sv.status/error | valid\|validation_error | 控制后续阶段是否执行。 | 始终产生。 |
| normalized_sv.{sv_id,genome_build,chrom,start,end,sv_type} | object | 验证并规范化后的不可变候选身份。 | 输入无效时不构造有效身份。 |
| normalized_sv.{genome_build_original,sv_type_original,sv_subtype,normalizations} | object | 标准化前值、移动元件亚型与变更审计。 | 有效输入时产生。 |
| normalized_sv.{coordinate_system,chromosome_length_bp,length_bp} | object | 1-based inclusive 约定、染色体边界和长度。 | INS/BND 未给长度时 length_bp 为 null。 |
| normalized_sv.{cipos,ciend,start_confidence_interval,end_confidence_interval,breakpoint_uncertainty_status,imprecise} | object | 相对 CI、裁剪后的绝对 CI 及完整度。 | CI 为 null，状态为 not_provided。 |
| normalized_sv.{bnd_mate_status,mate_chrom,mate_pos,mate_confidence_interval,local_orientation,mate_orientation} | object | 解析后的 BND 第二断点和邻接方向。 | 无 mate 时显式 not_provided。 |
| normalized_sv.{statistics,quality,source_record,warnings} | object | 不解释地保留上游统计、质量和来源。 | 缺失项进入 warnings。 |

处理规则：

- **核心解析与边界校验**（deterministic）：解析 JSON，标准化 build/chrom/SVTYPE，验证整数、顺序、正长度和染色体范围；固定 1-based inclusive。
  - 分支/约束：无效输入返回 validation_error
- **CI 与 BND 标准化**（deterministic）：相对 CI 转绝对坐标并裁剪；解析四种 BND ALT 或显式 mate；可选无效 mate 只警告。
  - 分支/约束：缺 CI 不伪造测量区间
  - 分支/约束：缺 mate 保留 first-breakend-only
- **保留原值与上下文**（deterministic）：记录别名映射，原样保留统计、质量和 source_record。

实现位置：`prompts.py:INTAKE / state_pipeline.py:normalize_and_store`

## 2. 不可跳过的证据基线

一次固定调用并发收集 Ensembl overlap/VEP、gnomAD-SV、ClinGen Dosage、ClinVar、dbVar、DGV Gold 和技术风险；工具直接保存带证据 ID 的完整结果。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| baseline_evidence.{collection_policy,immutable_candidate_fields} | object | 声明基线不可跳过，并复制不得被自适应阶段修改的候选字段。 | 有效输入时产生。 |
| baseline_evidence.region_annotation.features | gene/regulatory/repeat records\|null | 名义区间的 Ensembl 空间重叠；记录带 ENS-BL ID。 | 空数组=成功无记录；null=查询失败。 |
| baseline_evidence.region_annotation.breakpoint_annotations.{start,end,mate} | object | 由 VCF CI 或带标签 fallback 构造的各断点窗口及 overlap 结果。 | 无 BND mate 时 mate 为 null。 |
| baseline_evidence.region_annotation.{errors,truncated,attempts,source_urls,completeness,limitations} | object | Ensembl 逐类错误、截断、尝试次数、来源与空间重叠限制。 | 重试耗尽仍保持 error/null，不转成 not_found。 |
| baseline_evidence.vep_evidence.records[] | VEP-BL evidence records | VEP 转录本/调控/motif/intergenic consequence、impact、overlap、canonical/MANE 和 exon/intron 信息。 | BND、方向未知 CNV 或超出区间上限时显式 not_applicable。 |
| baseline_evidence.vep_evidence.{input_annotations,consequence_count,records_truncated,attempts,retrieved_at,limitations} | object | VEP 输入级最严重 consequence、原始计数、截断、尝试和预测边界。 | 失败显式 error，不转成无 consequence。 |
| baseline_evidence.database_evidence.records[] | GNO-BL evidence records | gnomAD-SV 坐标、类型、AC/AN/AF、filters、匹配类别与指标。 | 成功无候选时为空数组。 |
| baseline_evidence.database_evidence.{dataset,query_regions,breakpoint_windows,matching_query_regions} | object | build 对应数据集、实际检索区域与固定匹配窗口。 | API 失败时保留 query_errors。 |
| baseline_evidence.database_evidence.{counts,query_errors,retrieved_at,limitations} | object | 筛选计数、失败、检索时间和同一事件判定限制。 | 始终保留状态。 |
| baseline_evidence.clingen_dosage_evidence.records[] | CGD-BL evidence records | ClinGen 基因/区域的 HI、TS 评分、在线报告与区间匹配指标。 | 成功无重叠时为空数组；不适用 SVTYPE 显式 not_applicable。 |
| baseline_evidence.clingen_dosage_evidence.{dataset_created_at,counts,retrieved_at,limitations} | object | ClinGen 下载文件日期、筛选计数、检索时间与临床解释边界。 | 下载或解析失败显式 error。 |
| baseline_evidence.clinvar_evidence.records[] | CLV-BL evidence records | ClinVar VCV、临床分类、review status、性状、提交计数、坐标及区间匹配指标。 | 成功无候选时为空数组。 |
| baseline_evidence.clinvar_evidence.{query_regions,search_terms,counts,query_errors,retrieved_at,limitations} | object | 实际检索区间和检索式、命中/返回计数、失败与 ClinVar 解释限制。 | 失败与无记录严格区分。 |
| baseline_evidence.dbvar_evidence.records[] | DBV-BL evidence records | dbVar 变异/研究 accession、build placement、变异类型、方法、基因、临床字段及匹配指标。 | BND 显式 not_applicable；成功无候选为空数组。 |
| baseline_evidence.dbvar_evidence.{query_regions,query_terms,search_counts,query_errors,retrieved_at,limitations} | object | dbVar 有界端点检索、总命中/截断、错误以及异质研究和 remap 限制。 | 失败与无记录严格区分。 |
| baseline_evidence.dgv_evidence.records[] | DGV-BL evidence records | DGV Gold 变异类型、频率、样本/研究计数、来源摘要及区间匹配指标。 | 成功无候选时为空数组；BND 显式 not_applicable。 |
| baseline_evidence.dgv_evidence.{dataset,backend,query_regions,counts,query_errors,retrieved_at,limitations} | object | DGV Gold/UCSC 后端、实际查询、筛选计数、失败和版本/覆盖限制。 | API 失败显式 error。 |
| baseline_evidence.artifact_risk.{overall_risk,risk_items} | object | call rate、caller、repeat、mappability、reads、GQ、batch 的确定性初筛。 | 数据不足保持 unknown。 |

处理规则：

- **固定基线调用门**（deterministic）：工具从状态读取标准化输入，直接保存完整基线结果；无效输入记录 blocked，模型不负责转写。
  - 分支/约束：validation_error → blocked
- **Ensembl 基线 overlap**（external-query）：重新校验坐标后查询名义区间及 start/end/mate 窗口的 gene、regulatory、repeat；相同区间复用，瞬时错误有限重试、全局限并发；保留错误、尝试次数、截断、URL 和 ENS-BL ID。
  - 分支/约束：CI 缺失使用带标签 ±500 bp fallback
  - 分支/约束：重试耗尽保留 error，不当作无注释
- **Ensembl VEP consequence**（external-query）：将 build、区间、strand 和符号 DEL/DUP/INV/INS 提交给 VEP；按 impact、MANE、canonical 和覆盖率排序并压缩 consequence，添加 VEP-BL ID。
  - 分支/约束：BND 与方向未知 CNV 返回 not_applicable
  - 分支/约束：超过 SV_AGENT_MAX_VEP_INTERVAL_BP 返回 not_applicable
  - 分支/约束：预测 consequence 不等于实验或临床结论
- **gnomAD-SV 基线与固定匹配**（external-query）：重新校验已存候选坐标；按 build 选数据集，检索候选并用类型、重叠和断点规则分类；缺失 CI 时 ±500 bp 只扩展检索，不单独提升 high_similarity；添加 GNO-BL ID。
  - 分支/约束：BND 有 mate 比较双端；无 mate 只比较第一端且不能确认同一事件
- **ClinGen Dosage 基因与区域证据**（external-query）：下载 ClinGen 当前基因与区域剂量敏感性表，按 build 解析区间并计算重叠；DEL 优先 HI、DUP 优先 TS，记录评分、报告链接、版本日期、匹配指标和 CGD-BL ID。
  - 分支/约束：非 CNV 类型返回 not_applicable
  - 分支/约束：空间重叠和剂量评分不能直接诊断当前个体
- **ClinVar 临床变异记录**（external-query）：使用 NCBI E-utilities 按 build、区间、SV 类型和长度检索 VCV，提取临床分类、review status、性状、提交计数与坐标，再以统一规则计算 overlap/断点指标并添加 CLV-BL ID。
  - 分支/约束：大区间和返回数量均受硬限制
  - 分支/约束：BND 只比较当前可检索断点，不能仅凭命中确认同一邻接事件
  - 分支/约束：检索失败不当作无记录
- **NCBI dbVar 结构变异记录**（external-query）：以 NCBI ESearch/ESummary 按染色体、端点、类型和对象检索，筛选 build-matched placement，计算固定匹配指标并添加 DBV-BL ID。
  - 分支/约束：泛 CNV 对 DEL/DUP 仅标为方向不明
  - 分支/约束：BND 因无可靠 mate adjacency 返回 not_applicable
  - 分支/约束：端点检索可能漏掉完全包围候选的更大记录
  - 分支/约束：remap 和坐标相同不证明事件同一或已验证
- **DGV Gold 人群结构变异**（external-query）：通过 UCSC API 查询 build 对应的 dgvGold track，将 0-based half-open 坐标转为 1-based inclusive，按类型与区间匹配并压缩冗长样本/来源字段，添加 DGV-BL ID。
  - 分支/约束：BND 返回 not_applicable
  - 分支/约束：dgvGold 不是 DGV 完整当前发布，阴性结果不能证明数据库中不存在
- **确定性技术风险**（deterministic）：根据质量字段和断点 repeat 判断风险；布尔伪数字或范围外 call rate 不参与数值判定。
  - 分支/约束：缺失、类型错误或范围错误保持 unknown

实现位置：`prompts.py:BASELINE / state_pipeline.py:baseline_and_store`

## 3. 受约束的自适应调查

LLM 选择 0–2 个后续动作并解释；工具原始结果另存 adaptive_tool_results，不由模型转写。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| adaptive_investigation.identified_evidence_gaps | string[] | LLM 从基线中识别的具体未决问题。 | 没有实质缺口时为空。 |
| adaptive_investigation.planned_actions | action[] | 每个候选动作的缺口、理由和预期信息增益。 | 没有合格动作时为空。 |
| adaptive_tool_results[] | audited action[] | 工具直接写入状态的完整执行/拒绝记录、预算与真实结果；模型不转写。 | 零调用时为空。 |
| adaptive_tool_results[].result.result.Ensembl | ENS-ADP records | 可选最近基因、transcript、exon 或 BND mate transcript 空间重叠。 | 未选动作或无记录时为空。 |
| adaptive_tool_results[].result.result.gnomAD-SV | GNO-ADP records | 扩大 2/10 kb 检索后取得的新候选；匹配窗口和阈值保持不变。 | 未选动作或无记录时为空。 |
| adaptive_investigation.{stop_reason,remaining_limitations} | object | 为何停止以及工具白名单仍无法解决的问题。 | 必须给出 stop_reason。 |

处理规则：

- **识别缺口与选择动作**（model-controlled）：只有缺口明确、工具能减少不确定性、未重复、预算存在且可能改变解释时才计划动作；P0/P1 固定来源已在基线查询，不重复调用。
  - 分支/约束：无合格动作直接停止
- **白名单、去重与硬预算**（deterministic）：先以短锁原子预留 ToolContext state 中的名额，再执行外部请求；强制最多 2 次并直接保存每次工具返回，拒绝非白名单和重复动作。
  - 分支/约束：拒绝项不执行外部查询
  - 分支/约束：外部失败仍消耗已预留预算
- **可选 Ensembl 精化**（external-query）：按已选动作查询 10/50 kb 最近基因、transcript、exon 或 BND mate transcript；瞬时错误有限重试，保留尝试次数和 ENS-ADP ID。
  - 分支/约束：BND mate action 无 mate 时 not_applicable
  - 分支/约束：重试耗尽保留 error
  - 分支/约束：重叠不等于 consequence
- **可选 gnomAD 检索扩展**（external-query）：只将 API 检索区域扩大 2 kb 或 10 kb；分类仍使用基线固定窗口与阈值。
  - 分支/约束：新取得但窗外的记录仍为 nearby
- **停止与剩余限制**（model-controlled）：说明停止原因和白名单无法覆盖的剩余问题，不把未用预算描述为失败。

实现位置：`prompts.py:ADAPTIVE / state_pipeline.py:adaptive_and_store`

## 4. 自适应文献检索

LLM 选择 PubMed 查询；工具硬性限制最多 3 个不同查询、每次默认 5 篇并跨查询去重 PMID；结果另存 literature_tool_results。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| literature_evidence.queries | string[0..3] | 区域/SVTYPE 和实际返回基因驱动的透明 PubMed 查询。 | 无有用查询时为空。 |
| literature_tool_results[].records[] | PMID metadata[] | 工具保存去重后的 PMID、标题、前三位作者姓名、作者总数、期刊、日期、DOI、URL 和 PMID 证据 ID。 | 未命中为空；失败显式 error。 |
| literature_tool_results[].{query_budget,queries_used,queries_remaining,duplicate_pmids_excluded,returned_record_count} | object | 程序级查询预算和跨查询 PMID 去重计数；被拒绝的调用不触发 API。 | 无查询时结果列表为空。 |
| literature_evidence.{missing_sources,limitations} | object | 未实现来源和标题级证据限制。 | 按需产生。 |

处理规则：

- **证据驱动 PubMed 查询**（external-query）：以短锁原子预留查询名额并合并去重结果；限制最多 3 个不同查询、每次默认 5 篇，压缩作者信息并保存证据 ID、计数和错误。
  - 分支/约束：重复查询或超预算拒绝且不访问 API
  - 分支/约束：异常响应显式 error，不伪装为无记录
  - 分支/约束：失败查询仍占一个名额
  - 分支/约束：不得从模型记忆补基因

实现位置：`prompts.py:LITERATURE / state_pipeline.py:literature_and_store`

## 5. 证据核验

把陈述拆成原子 claim，核验 evidence ID，拒绝无证据事实与过度解释。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| verification.{supported_claims,rejected_claims} | VerifiedClaim[] | 带 evidence ID、claim 类型、置信度和核验状态的原子陈述。 | 默认空数组。 |
| verification.{publication_allowed,contradictions,missing_evidence,warnings} | object | 发布门、矛盾、缺证和核验警告。 | schema 要求 publication_allowed。 |

处理规则：

- **原子 claim 与证据核验**（model-structured）：事实 claim 必须引用已有 ID；区分 observation/database_fact/inference/hypothesis 并拒绝过度解释。
  - 分支/约束：VEP consequence 不能表述为已证实机制
  - 分支/约束：ClinVar review status 与冲突必须保留
  - 分支/约束：dbVar overlap 不证明验证或临床意义
  - 分支/约束：ClinGen/DGV/gnomAD 不能被单独提升为个体致病或良性结论
  - 分支/约束：检索扩展不能改变匹配语义
  - 分支/约束：标题不能支持机制

实现位置：`prompts.py:VERIFY / schemas.py:VerificationOutput`

## 6. 最终报告

生成带证据目录、来源和自适应调查日志的结构化报告，并做确定性 schema 校验。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| final_report.sv_summary | SVSummary | 只复制标准化候选身份、CI 和 BND 字段。 | 无效输入保留可用原字段并 blocked。 |
| final_report.*_evidence/artifact_risks/possible_interpretations | ReportStatement[] | 按统计、区域、人群、文献、功能、技术风险和解释组织的有证据陈述。 | 默认空数组。 |
| final_report.{evidence_catalog,query_provenance} | object | 被引用证据与外部查询来源目录；ID 必须唯一且可解析。 | 无引用时为空。 |
| final_report.investigation_log | InvestigationLog | 复制证据缺口、计划、执行动作、2 次预算、停止原因和剩余限制。 | 必填并经 schema 校验。 |
| final_report.{report_version,report_status,limitations,recommended_next_steps} | object | 报告版本、完成状态、限制和可复现下一步。 | schema 强制状态。 |

处理规则：

- **按证据编排报告**（model-structured）：只组合前序状态；复制调查审计；不恢复 rejected claim，不凭模型记忆补证据。
  - 分支/约束：输入无效 blocked；重要缺失 incomplete
- **Pydantic 确定性验证**（schema-validation）：验证候选坐标、证据 ID 引用唯一性以及固定为 2 的 adaptive 预算；queries_used 必须等于真正执行的动作数，拒绝动作只保留审计。
  - 分支/约束：悬空 evidence ID、越界坐标、动作计数不一致或超预算报告被拒绝

实现位置：`prompts.py:REPORT / schemas.py:SVReport`

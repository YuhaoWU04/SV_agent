# SV Investigator 字段词典

> 自动生成自 `architecture/data_lineage.json`；源指纹 `4b92d08d4c4b`。
> 请勿直接编辑本文件。

## 0. 用户输入

接收坐标、参考基因组、SVTYPE、断点不确定性、统计和质量信息。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| input.{genome_build,chrom,start,end,sv_type} | object | 候选身份的五个必填字段。 | 任一缺失即 validation_error。 |
| input.{CIPOS,CIEND,CIMATE,IMPRECISE} | object\|null | VCF 断点不确定性及不精确标志。 | 下游使用明确标记的 ±500 bp fallback。 |
| input.{ALT,mate_chrom,mate_pos,CHR2,END} | object\|null | BND mate 坐标与方向来源。 | BND 降级为 first-breakend-only。 |
| input.{sv_id,length_bp,statistics,quality,source_record} | object\|null | 上游标识、长度、统计、质量和原 VCF 记录。 | 保留显式 warning 或空对象。 |

处理规则：

- 此阶段只提供外部输入字段。

实现位置：`README.md / tools.py:normalize_sv_input`

## 1. 确定性标准化

统一 build、染色体与 SVTYPE，验证坐标，解析 CI 和 BND mate，同时保留原值。

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

实现位置：`prompts.py:INTAKE / tools.py:normalize_sv_input`

## 2. 不可跳过的证据基线

一次固定调用收集 Ensembl、gnomAD-SV 和技术风险；完整保留原始记录并加证据 ID。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| baseline_evidence.{collection_policy,immutable_candidate_fields} | object | 声明基线不可跳过，并复制不得被自适应阶段修改的候选字段。 | 有效输入时产生。 |
| baseline_evidence.region_annotation.features | gene/regulatory/repeat records\|null | 名义区间的 Ensembl 空间重叠；记录带 ENS-BL ID。 | 空数组=成功无记录；null=查询失败。 |
| baseline_evidence.region_annotation.breakpoint_annotations.{start,end,mate} | object | 由 VCF CI 或带标签 fallback 构造的各断点窗口及 overlap 结果。 | 无 BND mate 时 mate 为 null。 |
| baseline_evidence.region_annotation.{errors,truncated,source_urls,completeness,limitations} | object | Ensembl 逐类错误、截断、来源与空间重叠限制。 | 错误保持 error/null，不转成 not_found。 |
| baseline_evidence.database_evidence.records[] | GNO-BL evidence records | gnomAD-SV 坐标、类型、AC/AN/AF、filters、匹配类别与指标。 | 成功无候选时为空数组。 |
| baseline_evidence.database_evidence.{dataset,query_regions,breakpoint_windows,matching_query_regions} | object | build 对应数据集、实际检索区域与固定匹配窗口。 | API 失败时保留 query_errors。 |
| baseline_evidence.database_evidence.{counts,query_errors,retrieved_at,limitations} | object | 筛选计数、失败、检索时间和同一事件判定限制。 | 始终保留状态。 |
| baseline_evidence.artifact_risk.{overall_risk,risk_items} | object | call rate、caller、repeat、mappability、reads、GQ、batch 的确定性初筛。 | 数据不足保持 unknown。 |

处理规则：

- **固定基线调用门**（model-controlled）：有效输入必须且只能调用 collect_baseline_evidence 一次；模型不能删减来源或重写记录。
  - 分支/约束：validation_error → blocked
- **Ensembl 基线 overlap**（external-query）：查询名义区间及 start/end/mate 窗口的 gene、regulatory、repeat；保留错误、截断、URL 和 ENS-BL ID。
  - 分支/约束：CI 缺失使用带标签 ±500 bp fallback
- **gnomAD-SV 基线与固定匹配**（external-query）：按 build 选数据集，检索候选并用固定窗口/类型/重叠/双断点规则分类，添加 GNO-BL ID。
  - 分支/约束：BND 有 mate 比较双端；无 mate 只比较第一端且不能确认同一事件
- **确定性技术风险**（deterministic）：根据质量字段和断点 repeat 判断风险；缺数据保持 unknown。

实现位置：`prompts.py:BASELINE / tools.py:collect_baseline_evidence`

## 3. 受约束的自适应调查

LLM 根据基线识别证据缺口，从真实工具白名单选择 0–2 个非重复后续动作。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| adaptive_investigation.identified_evidence_gaps | string[] | LLM 从基线中识别的具体未决问题。 | 没有实质缺口时为空。 |
| adaptive_investigation.planned_actions | action[] | 每个候选动作的缺口、理由和预期信息增益。 | 没有合格动作时为空。 |
| adaptive_investigation.executed_actions | audited action[] | 工具记录的执行/拒绝状态、预算使用和真实结果。 | 零调用时为空。 |
| executed_actions[].result.Ensembl | ENS-ADP records | 可选最近基因、transcript、exon 或 BND mate transcript 空间重叠。 | 未选动作或无记录时为空。 |
| executed_actions[].result.gnomAD-SV | GNO-ADP records | 扩大 2/10 kb 检索后取得的新候选；匹配窗口和阈值保持不变。 | 未选动作或无记录时为空。 |
| adaptive_investigation.{stop_reason,remaining_limitations} | object | 为何停止以及工具白名单仍无法解决的问题。 | 必须给出 stop_reason。 |

处理规则：

- **识别缺口与选择动作**（model-controlled）：只有缺口明确、工具能减少不确定性、未重复、预算存在且可能改变解释时才计划动作。
  - 分支/约束：无合格动作直接停止
- **白名单、去重与硬预算**（deterministic）：ToolContext state 强制最多 2 次；拒绝非白名单和重复动作；外部失败也消耗预算并进入审计。
  - 分支/约束：拒绝项不执行外部查询
- **可选 Ensembl 精化**（external-query）：按已选动作查询 10/50 kb 最近基因、transcript、exon 或 BND mate transcript，保留 ENS-ADP ID。
  - 分支/约束：BND mate action 无 mate 时 not_applicable
  - 分支/约束：重叠不等于 consequence
- **可选 gnomAD 检索扩展**（external-query）：只将 API 检索区域扩大 2 kb 或 10 kb；分类仍使用基线固定窗口与阈值。
  - 分支/约束：新取得但窗外的记录仍为 nearby
- **停止与剩余限制**（model-controlled）：说明停止原因和白名单无法覆盖的剩余问题，不把未用预算描述为失败。

实现位置：`prompts.py:ADAPTIVE / tools.py:run_budgeted_adaptive_action`

## 4. 自适应文献检索

根据候选区域以及实际查到的基因构造至多三个 PubMed 查询。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| literature_evidence.queries | string[0..3] | 区域/SVTYPE 和实际返回基因驱动的透明 PubMed 查询。 | 无有用查询时为空。 |
| literature_evidence.records[] | PMID metadata[] | PMID、标题、作者、期刊、日期、DOI 和 URL。 | 未命中为空；失败显式 error。 |
| literature_evidence.{missing_sources,limitations} | object | 未实现来源和标题级证据限制。 | 按需产生。 |

处理规则：

- **证据驱动 PubMed 查询**（external-query）：使用区域/SVTYPE 和实际返回基因构造至多三个查询；保存 PMID 元数据和限制。
  - 分支/约束：不得从模型记忆补基因

实现位置：`prompts.py:LITERATURE / tools.py:search_pubmed`

## 5. 证据核验

把陈述拆成原子 claim，核验 evidence ID，拒绝无证据事实与过度解释。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| verification.{supported_claims,rejected_claims} | VerifiedClaim[] | 带 evidence ID、claim 类型、置信度和核验状态的原子陈述。 | 默认空数组。 |
| verification.{publication_allowed,contradictions,missing_evidence,warnings} | object | 发布门、矛盾、缺证和核验警告。 | schema 要求 publication_allowed。 |

处理规则：

- **原子 claim 与证据核验**（model-structured）：事实 claim 必须引用已有 ID；区分 observation/database_fact/inference/hypothesis 并拒绝过度解释。
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
- **Pydantic 确定性验证**（schema-validation）：验证候选字段、证据 ID 引用唯一性以及 adaptive queries_used ≤ query_budget ≤ 2。
  - 分支/约束：悬空 evidence ID 或超预算报告被拒绝

实现位置：`prompts.py:REPORT / schemas.py:SVReport`

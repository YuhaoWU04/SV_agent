# SV Investigator 字段词典

> 自动生成自 `architecture/data_lineage.json`；源指纹 `fa78db4089a0`。
> 请勿直接编辑本文件。

## 0. 用户输入

接收坐标、参考基因组、SVTYPE、断点不确定性、统计和质量信息。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| input.{genome_build,chrom,start,end,sv_type} | object | 候选身份的五个必填字段。 | 任一缺失即 validation_error。 |
| input.{CIPOS,CIEND,CIMATE,IMPRECISE} | object\|null | VCF 断点不确定性及不精确标志；[0,0] 表示零宽区间，不表示缺失。 | 省略或设为 null；下游仅用带标签的 ±500 bp fallback 检索附近候选。 |
| input.{ALT,mate_chrom,mate_pos,CHR2,END} | object\|null | BND mate 坐标与方向来源。 | BND 降级为 first-breakend-only。 |
| input.{sv_id,length_bp,statistics,quality,source_record} | object\|null | 上游标识、长度、统计、质量和原 VCF 记录；可提供 source_record.info_definition 的 ID→描述字典，Fst 导出时从 header 提取当前记录所含字段的说明。 | 保留显式 warning 或空对象；缺少说明字典不要求调用模型解释。 |

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
| normalized_sv.{statistics,quality,source_record,warnings} | object | 保留上游统计、质量及原始 INFO；程序为当前 INFO 字段解析 info_definition，输入说明优先，再按明确的 1000G-SV 来源及通用 VCF 字典补缺；保留 description/source，不由 LLM 猜缩写。 | 缺失项进入 warnings；未知字段不编造说明，无 INFO 的 SV 不要求新增字典。 |

处理规则：

- **核心解析与边界校验**（deterministic）：解析 JSON，标准化 build/chrom/SVTYPE，验证整数、顺序、正长度和染色体范围；固定 1-based inclusive。
  - 分支/约束：无效输入返回 validation_error
- **CI 与 BND 标准化**（deterministic）：相对 CI 转绝对坐标并裁剪；解析四种 BND ALT 或显式 mate；可选无效 mate 只警告。
  - 分支/约束：缺 CI 不伪造测量区间
  - 分支/约束：缺 mate 保留 first-breakend-only
- **保留原值与上下文**（deterministic）：记录别名映射，保留统计、质量和原始 INFO。source_record.info_definition 仅包含当前字段，按 provided→1000g_dictionary→vcf_standard 逐字段解析；不覆盖输入描述，不认证调用方自称的描述来源，不给未知来源套用 MC 等专用定义。
  - 分支/约束：出现字段的输入描述格式错误时 validation_error
  - 分支/约束：定义不是独立生物学证据，不新增 evidence ID

实现位置：`prompts.py:INTAKE / state_pipeline.py:normalize_and_store`

## 2. 不可跳过的证据基线

一次固定调用并发收集 Ensembl overlap/VEP、gnomAD-SV、ClinGen Dosage、ClinVar、dbVar、DGV Gold、ENCODE cCRE、GeneHancer links、GTEx molecular QTL、断点 mappability 和技术风险；工具直接保存带证据 ID 的完整结果。

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
| baseline_evidence.{regulatory_element_evidence,regulatory_gene_link_evidence,qtl_evidence,mappability_evidence} | CCRE/REG/QTL/MAP evidence records and audit | ENCODE4 cCRE、GeneHancer 调控端点与靶基因连接、GTEx 区域 eQTL 与最多三个变异的 sQTL follow-up、build 对应 100-mer 断点 mappability；保留证据 ID、范围、组织、统计量、覆盖率、来源和限制。 | 失败与无记录严格区分；GRCh37 的 cCRE/QTL 显式 not_applicable，不自动 liftover。 |
| baseline_evidence.artifact_risk.{overall_risk,risk_items} | object | caller、repeat、mappability、reads、GQ、batch 的确定性初筛；call rate 只作为 INPUT-STAT。 | 数据不足保持 unknown；非单位 mappability 分数不机械判风险。 |

处理规则：

- **固定基线调用门**（deterministic）：工具从状态读取标准化输入，直接保存完整基线结果；无效输入记录 blocked，模型不负责转写。
  - 分支/约束：validation_error → blocked
- **Ensembl 基线 overlap**（external-query）：重新校验坐标后查询名义区间及 start/end/mate 窗口；每个范围先合并取回 gene、regulatory、repeat，失败后串行拆分查询以保留部分结果；所有 Ensembl 请求全局串行并共享指数退避冷却，保留错误、尝试次数、截断、URL 和 ENS-BL ID。
  - 分支/约束：CI 缺失使用带标签 ±500 bp fallback
  - 分支/约束：合并查询失败后降级为逐类查询
  - 分支/约束：重试耗尽保留 error，不当作无注释
- **Ensembl VEP consequence**（external-query）：将 build、区间、strand 和符号 DEL/DUP/INV/INS 提交给 VEP，其中点状 INS 转为 VEP 的 start=end+1 表示；按 impact、MANE、canonical 和覆盖率排序并压缩 consequence，添加 VEP-BL ID。
  - 分支/约束：BND 与方向未知 CNV 返回 not_applicable
  - 分支/约束：超过 SV_AGENT_MAX_VEP_INTERVAL_BP 返回 not_applicable
  - 分支/约束：预测 consequence 不等于实验或临床结论
- **gnomAD-SV 基线与固定匹配**（external-query）：重新校验已存候选坐标；按 build 选数据集，检索候选并用类型、重叠和断点规则分类；起止偏移按数据库坐标减输入坐标保留正负方向，排序使用绝对值；缺失 CI 时 ±500 bp 只扩展检索，不单独提升 high_similarity；添加 GNO-BL ID。
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
- **调控、分子 QTL 与可比对性**（external-query）：固定基线查询 UCSC build-matched tracks；连接记录按实际调控端点、eQTL 按实际 variant position 过滤而非连接跨度；QTL 检索区间向两侧各扩展 10 kb，scope 标为 padded 并保留 padding_bp，不混称名义区间。最多三个 eQTL 变异经 GTEx v8 查询 sQTL。mappability 计算断点窗口加权均值、最小值和覆盖率。returned_record_count 等于实际返回记录数。
  - 分支/约束：保留原始字段、证据 ID 与查询错误/截断
  - 分支/约束：异常 sQTL 行记录错误，保留其余有效记录
  - 分支/约束：区域 QTL 不推断 SV identity、LD 或 colocalization
  - 分支/约束：未测 mappability 不填零
- **确定性技术风险**（deterministic）：根据质量字段、断点 repeat 和实际 mappability 测量判断风险；完整覆盖且全为 1 时仅排除该参考轨道风险，其余不机械判为 present。
  - 分支/约束：缺失测量保持 unknown

实现位置：`prompts.py:BASELINE / state_pipeline.py:baseline_and_store`

## 3. 受约束的自适应调查

LLM 只选择 0–2 个后续动作并记录决策审计；工具原始结果另存 adaptive_tool_results，后续 synthesis 不依赖其生物学复述。

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
- **可选 Ensembl 精化**（external-query）：按动作查询最近基因、transcript、exon 或 BND mate transcript。短 SV 的 QUERY_EXONS 分别查询 nominal 和已提供的 start/end CI；无 CI 不新增窗口；大 SV 保留断点窗口策略。保留各范围状态、截断、尝试次数和 ENS-ADP ID。
  - 分支/约束：每个精化查询范围不得超过 5 Mb，超限保留 error
  - 分支/约束：部分失败或截断明确 completeness=partial，不作为全范围零命中
  - 分支/约束：BND mate action 无 mate 时 not_applicable
  - 分支/约束：重叠不等于 consequence
- **可选 gnomAD 检索扩展**（external-query）：只将 API 检索区域扩大 2 kb 或 10 kb；分类仍使用基线固定窗口与阈值。
  - 分支/约束：新取得但窗外的记录仍为 nearby
- **停止与剩余限制**（model-controlled）：说明停止原因和白名单无法覆盖的剩余问题，不把未用预算描述为失败。

实现位置：`prompts.py:ADAPTIVE / state_pipeline.py:adaptive_and_store`

## 4. 自适应文献检索

LLM 只选择 PubMed 查询并返回简短审计；坐标查询必须保留精确位点和 SVTYPE，不得放宽成染色体区带或综合征；工具硬限最多 3 个查询、每次默认 5 篇、跨查询去重 PMID。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| literature_evidence.queries | string[0..3] | 精确位点/SVTYPE 和实际返回基因驱动的透明 PubMed 查询；不放宽为区带或综合征。 | 无有用查询时为空。 |
| literature_tool_results[].records[] | PMID citation and abstract[] | 保存去重后的 PMID、标题、作者、刊物、日期、DOI 和证据 ID；现有检索批量补取 XML 摘要，按 PMID 对应，保留结构化段落标签、abstract_status 和摘要来源 URL。 | 摘要缺失记 not_found，请求/解析/记录缺失记 error 并保留 citation；不读取全文，不生成缺失摘要。 |
| literature_tool_results[].{query_budget,queries_used,queries_remaining,duplicate_pmids_excluded,returned_record_count} | object | 程序级查询预算和跨查询 PMID 去重计数；被拒绝的调用不触发 API。 | 无查询时结果列表为空。 |
| literature_evidence.{missing_sources,limitations} | object | 未实现来源、摘要获取状态及未读取全文的限制。 | 按需产生。 |

处理规则：

- **证据驱动 PubMed 查询**（external-query）：限制最多 3 个查询、每次 5 篇，原子预留名额并去重。搜索、摘要 metadata 和一次批量 EFetch 共用 NCBI 限速；XML 摘要按 PMID 对应，完整原文进入现有 view、核验查询和 catalog。部分 PMID metadata 未返回或摘要读取失败时 completeness=partial；无摘要但成功取得完整记录不算失败。
  - 分支/约束：重复查询或超预算拒绝且不访问 API
  - 分支/约束：摘要失败或缺失保留标题，不伪造正文
  - 分支/约束：失败查询仍占一个名额
  - 分支/约束：不读取全文，不把未取得的信息当作文献结论

实现位置：`prompts.py:LITERATURE / state_pipeline.py:literature_and_store`

## 5. 证据综合

程序先将工具证据按 ID 确定性索引，模型再总结现有证据能说明什么并产生原子候选 claim。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| evidence_view.{records_by_id,source_context} | object | 程序从三份工具状态生成的 ID→原记录索引和精简的来源状态、错误、计数与限制上下文。 | 无命中时 records_by_id 为空，失败和未查状态仍保留在 source_context。 |
| claim_synthesis.{candidate_claims,evidence_gaps,limitations} | SynthesisOutput | 带引用的原子候选 claim；每条 claim 预先指定 report_section，尚未核验。不额外生成自由文本总结，避免重复和放大结论。 | 无可支持陈述时 candidate_claims 为空。 |

处理规则：

- **确定性证据投影**（deterministic）：before-agent callback 遍历工具状态，将每条原记录按 evidence_id 唯一索引；原记录从 source_context 移出以避免 prompt 重复。
  - 分支/约束：完整原工具结果仍保留在 session state
  - 分支/约束：后三个 LLM agent 使用 include_contents=none，不重放工具历史
- **证据总结与原子 claim**（model-structured）：拆分原子 claim，引用实际字段/标题/摘要。INFO 缩写可能有歧义时，用 get_info_descriptions 按需取得原始值、已保存描述及释义来源，不新增输入展示副本。基因边界不单独支持内含子，基因检索命中不建立功能关联，未读全文不能判断实验不存在；Fst 单独提出的选择解释保留为假说。
  - 分支/约束：事实候选 claim 无 evidence ID 时由 schema 边界丢弃并记入 limitation，不中止 workflow
  - 分支/约束：相同证据范围规则适用于 gaps/limitations
  - 分支/约束：ClinVar 有界检索与 ClinGen 剂量敏感性是不同问题

实现位置：`agent.py:prepare_evidence_view / state_pipeline.py:build_evidence_view / prompts.py:SYNTHESIS / schemas.py:SynthesisOutput`

## 6. 证据核验

模型裁决完整 claim，核验假说依据与未验证联系，并批准可发布的 gaps/limitations；程序恢复原 claim，批准列表只接受 synthesis 原文子集，假说保留低置信度兜底。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| verification_evidence_view | bounded directory and audit | 精简目录、引用 ID、来源计数和查询状态；完整 evidence_view 仍留在 state，不把所有正文塞进核验 prompt。 | 目录超限明确 directory_truncated，仍可工具搜索完整存储。 |
| {verification_query_history,verification_loaded_ids} | deterministic lookup audit | 按 ID/字段投影获取或来源、类型、范围、文本、坐标搜索，不设固定调用次数预算；相同请求返回先前查询编号，不重复正文。每页上限 20，正文每次 8 条，响应上限 24000 字符；只读取已有证据，不访问外部数据库；runner 原有单例超时保留。 | 未知 ID、字段错误、超大记录、重复请求与分页显式标记；新候选清空查询状态。 |
| verification.{supported_claims,rejected_claims} | VerifiedClaim[] | 对候选 claim 的逐条裁决；agent 结束后统一处理文本 JSON 与 set_model_response 输出，恢复 synthesis 原文、分区、类型和 evidence ID，丢弃新增或改写。原始模型响应留在 event log。拒绝优先；rejected 列表内的正向 status 转为 unsupported 并记录原状态，不回流到报告。 | 默认空数组；漏裁决会阻止 complete 发布。 |
| verification.{publication_allowed,approved_evidence_gaps,approved_limitations,contradictions,missing_evidence,warnings} | object | 发布门、核验后的缺口与限制、矛盾、缺证和警告；批准列表只能包含 synthesis 原文，不允许新增或改写。 | schema 要求 publication_allowed；没有批准列表时不发布原始 gaps/limitations。 |

处理规则：

- **确定性证据查阅**（deterministic + local tools）：生成有界目录；模型用 get_evidence_by_ids 获取正文、search_stored_evidence 搜索漏引或冲突；保留来源限制与空间范围，查询分页/截断/错误及读取记录 ID 均有审计。INFO 缩写可能有歧义时，可用 get_info_descriptions 批量只读当前 normalized_sv 的值、描述和来源；缺失字段和未定义描述分开标记，不查询外部库，不添加调用预算。该元数据调用保留在 ADK event log，不混入 evidence-ID 读取审计。
  - 分支/约束：完整库不被引用子集覆盖
  - 分支/约束：查询结果不静默补写原 claim 引用
  - 分支/约束：局部缺证不等于数据库不存在
  - 分支/约束：INFO 说明不是独立生物学证据
- **候选 claim 证据核验**（model-structured + deterministic guard）：模型逐项检查实际标题/摘要/字段对各命题的支持，并批准 gaps/limitations。after_agent_callback 对两种最终输出统一恢复原文、拒绝优先；所有保留假说统一 low/partially_supported，原始拒绝不提升。
  - 分支/约束：未取回被引用正文的 claim 不能通过
  - 分支/约束：不借用基因检索词或不存在的摘要补支持
  - 分支/约束：verifier 不改假说正文，批准列表只接受 synthesis 原文子集
  - 分支/约束：名义区间和断点窗口不得混用
  - 分支/约束：成功零命中不得外推为全数据库或全文不存在

实现位置：`prompts.py:VERIFY / agent.py:bind_verification_to_synthesis / state_pipeline.py:reconcile_verification_from_state / schemas.py:VerificationOutput`

## 7. 最终报告

无 LLM 调用；程序组装核验 claim 和批准的 gaps/limitations；直接展示工具查询范围、数量和截断，不复制未核验的模型结论。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| final_report.sv_summary | SVSummary | 只复制标准化候选身份、CI 和 BND 字段。 | 无效输入保留可用原字段并 blocked。 |
| final_report.{gene_region_annotation,population_evidence,clinical_phenotype_evidence,literature_evidence,possible_interpretations,recommended_next_steps} | object | 事实分区只组装精确 supported claim；有限定说明的 partially_supported inference/hypothesis 可进入 possible_interpretations，保留假说统一 low。部分支持的事实原文只留在 JSON verified_claims 核查记录，Markdown 仅提示 claim ID，不再通过 Qualified findings 展示。下一步由批准的 evidence gap 生成。 | 无合格 claim 时对应分区为空。 |
| final_report.{statistical_signals,artifact_risks,verified_claims,contradictions} | object | 程序从 normalized/baseline/verification state 直接复制或格式化，不接受模型改写。 | 源字段缺失时为空。 |
| final_report.{evidence_catalog,query_provenance} | object | 程序生成被引用证据目录、used_by 和查询审计；审计包括 baseline/adaptive/literature 的范围、状态、数量、截断。请求成功不等于完整返回。 | 无引用时为空；未知 ID 被移除并写入 limitations；未报告截断时为 null，不假定完整。 |
| final_report.investigation_log | InvestigationLog | 计划理由作为审计保留；执行动作和预算由程序计数。发布的缺口与限制来自批准列表，停止摘要由程序生成，不复制模型的生物学停止结论。 | 必填并经 schema 校验。 |
| final_report.{report_version,report_status,limitations,recommended_next_steps} | object | 报告版本、完成状态、限制和可复现下一步。baseline、adaptive、literature 中任一失败、partial 或明确截断的查询使报告 incomplete，保留支持的发现并追加带范围限制；required baseline 明确 pending/blocked/error 时不能发布 complete；成功零命中本身不降低完成状态。完成状态不证明生物学结论正确。 | schema 强制状态。 |

处理规则：

- **确定性报告组装**（deterministic）：程序将核验 claim 分区，保留限定假说；组装时仅协调一次 verification（兼容旧文本 JSON），investigation_log 复用裁决。只从批准的 synthesis gaps/limitations 和 verifier 审查意见生成下一步与限制。查询范围、零命中、截断及数量由工具状态直接呈现；来源审计和 runner 指标共用固定基线来源清单。
  - 分支/约束：无最终 LLM 调用，不增加 agent 或重写循环
  - 分支/约束：预算只根据 adaptive_tool_results 中的 executed 动作计数
  - 分支/约束：不直接复制未核验的 synthesis 或 adaptive 结论
- **Pydantic 确定性验证**（schema-validation）：验证候选坐标、证据 ID 引用唯一性以及固定为 2 的 adaptive 预算；queries_used 必须等于真正执行的动作数，拒绝动作只保留审计。
  - 分支/约束：悬空 evidence ID、越界坐标、动作计数不一致或超预算报告被拒绝

实现位置：`agent.py:ReportAssemblyAgent / state_pipeline.py:finalize_report_from_state / schemas.py:SVReport`

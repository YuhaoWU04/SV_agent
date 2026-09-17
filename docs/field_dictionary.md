# SV Investigator 字段词典

> 自动生成自 `architecture/data_lineage.json`；源指纹 `1f9d544fd011`。
> 请勿直接编辑本文件。

## 0. 用户输入

接收候选 SV、统计量、质量信息和可选 VCF 字段。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| input.genome_build | string | 用户声明的参考基因组名称，可使用 hg19、hg38、GRCh37/38 等别名。 | 必填；缺失时 validation_error。 |
| input.chrom | string | 候选 SV 的第一染色体。 | 必填。 |
| input.start | integer\|string integer | 1-based inclusive 起点；BND 时是本地 breakend。 | 必填。 |
| input.end | integer\|string integer | 1-based inclusive 终点；传统 BND 输入仍保留该字段。 | 必填。 |
| input.sv_type | string | SV 类型或别名，例如 DEL、deletion、ALU、translocation。 | 必填。 |
| input.sv_id | string\|null | 用户提供的候选 SV 标识。 | 缺失时按 chrom:start-end:type 生成。 |
| input.length_bp / input.svlen | integer\|null | 可选 SV 长度；SVLEN 允许负号并取绝对值。 | 非 INS/BND 可由坐标跨度确定。 |
| input.CIPOS | [integer, integer]\|string\|null | 相对 start 的断点置信区间偏移。 | 下游改用带标记的启发式窗口。 |
| input.CIEND | [integer, integer]\|string\|null | 相对 end 的断点置信区间偏移；BND 可作为 mate CI。 | 下游改用带标记的启发式窗口。 |
| input.IMPRECISE | flag\|null | VCF 不精确断点标志。 | 按 false 保存。 |
| input.ALT | string\|null | VCF ALT；标准方括号 BND 表达可携带 mate 坐标和邻接方向。 | BND 可使用显式 mate 字段或降级。 |
| input.mate_chrom/mate_pos \| chrom2/pos2 \| CHR2/END | string+integer\|null | BND 第二断点的显式坐标。 | BND 降级为 first-breakend-only。 |
| input.CIMATE | [integer, integer]\|null | 相对 BND mate_pos 的置信区间偏移。 | 若存在 mate，回退使用 CIEND。 |
| input.statistics | object\|null | FST、病例/对照频率等上游统计信号，原样保留。 | 记录 statistics_not_provided。 |
| input.quality | object\|null | call_rate、caller、supporting_reads、genotype_quality、batch_checked 等质量信息。 | 记录 quality_not_provided，风险项保持 unknown。 |

处理规则：

- 此阶段只提供外部输入字段。

实现位置：`example_input.json`

## 1. 输入标准化

验证输入，统一参考基因组、染色体、SVTYPE 和断点表达，并保留审计信息。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| normalized_sv.status | valid\|validation_error | 标准化是否成功；控制所有后续阶段是否执行。 | 始终产生。 |
| normalized_sv.error | string\|null | 验证失败原因。 | 有效输入时不存在。 |
| normalized_sv.sv_id | string | 保留或自动生成的候选 SV 标识。 | 自动生成。 |
| normalized_sv.genome_build | GRCh37\|GRCh38 | 规范化后的参考基因组。 | 无有效值时整个输入失败。 |
| normalized_sv.genome_build_original | string | 标准化前的参考基因组名称，用于审计。 | 有效输入时保留。 |
| normalized_sv.chrom | 1-22\|X\|Y\|MT | 去除 chr 前缀并统一大小写后的主染色体。 | 无有效值时输入失败。 |
| normalized_sv.start | integer | 验证后的 1-based inclusive 起点。 | 无有效值时输入失败。 |
| normalized_sv.end | integer | 验证后的 1-based inclusive 终点。 | 无有效值时输入失败。 |
| normalized_sv.coordinate_system | 1-based-inclusive | 整个系统固定使用的坐标约定。 | 固定产生。 |
| normalized_sv.chromosome_length_bp | integer | 所选 build 和染色体的主染色体长度，用于边界校验和 CI 裁剪。 | 有效输入时产生。 |
| normalized_sv.sv_type | DEL\|DUP\|INV\|INS\|BND\|CNV | 规范化后的 SVTYPE。 | 无法识别时输入失败。 |
| normalized_sv.sv_type_original | string | 用户最初提供的 SV 类型。 | 有效输入时保留。 |
| normalized_sv.sv_subtype | ALU\|LINE1\|SVA\|MEI\|null | 移动元件等更细的插入亚型。 | 没有可识别亚型时为 null。 |
| normalized_sv.length_bp | integer\|null | DEL/DUP/INV/CNV 使用 inclusive span；INS/BND 只接受显式长度。 | INS/BND 未提供时为 null。 |
| normalized_sv.cipos | [integer, integer]\|null | 解析后的 CIPOS 相对偏移。 | 为 null。 |
| normalized_sv.ciend | [integer, integer]\|null | 解析后的 CIEND 相对偏移。 | 为 null。 |
| normalized_sv.start_confidence_interval | [integer, integer]\|null | start + CIPOS 后并裁剪至染色体边界的绝对坐标区间。 | 下游用 ± tolerance 检索。 |
| normalized_sv.end_confidence_interval | [integer, integer]\|null | end + CIEND 后并裁剪至染色体边界的绝对坐标区间。 | 下游用 ± tolerance 检索。 |
| normalized_sv.breakpoint_uncertainty_status | complete\|partial\|not_provided | CIPOS/CIEND 的提供完整度。 | 固定产生。 |
| normalized_sv.imprecise | boolean | 解析后的 IMPRECISE 标志。 | false。 |
| normalized_sv.bnd_mate_status | coordinates_provided\|not_provided\|not_applicable | 是否取得 BND mate 坐标。 | 非 BND 为 not_applicable。 |
| normalized_sv.mate_chrom | chromosome\|null | 解析并验证后的 BND 第二染色体。 | null。 |
| normalized_sv.mate_pos | integer\|null | 解析并验证后的 BND 第二断点坐标。 | null。 |
| normalized_sv.mate_confidence_interval | [integer, integer]\|null | mate_pos + CIMATE/CIEND 后的绝对坐标区间。 | gnomAD/Ensembl 使用启发式窗口。 |
| normalized_sv.local_orientation / mate_orientation | +\|-\|null | 从四种 VCF BND ALT 方括号形式解析的邻接方向。 | 显式 mate 无 ALT 时为 null。 |
| normalized_sv.breakpoint_fallback_tolerance_bp / policy | integer+string | 缺少测量 CI 时的候选检索容差及免责声明，默认 500 bp。 | 固定产生。 |
| normalized_sv.statistics | object | 原样保留的统计信号。 | 空对象。 |
| normalized_sv.quality | object | 原样保留的质量信息。 | 空对象。 |
| normalized_sv.warnings / normalizations | string[] | 缺失提示、容错降级和所有名称标准化记录。 | 空数组。 |

处理规则：

- **解析与必填验证**（deterministic）：解析 JSON；要求五个核心字段；整数、主染色体、坐标顺序或范围不合法则返回 validation_error。
  - 分支/约束：validation_error 会使后续阶段 blocked
- **名称标准化**（deterministic）：忽略 build 大小写和常见分隔符；去除 chr；映射 SVTYPE 与移动元件别名；保留原值和变更记录。
- **坐标与长度**（deterministic）：固定 1-based inclusive；检查染色体边界；普通区间长度=end-start+1；INS/BND 不推断长度。
  - 分支/约束：提供长度与普通区间跨度不同时产生 warning
- **断点置信区间**（deterministic）：解析两个相对偏移；分别加到 start/end；裁剪至染色体边界；根据提供程度标记 complete/partial/not_provided。
  - 分支/约束：缺失 CI 时只声明下游启发式检索规则，不伪造测量 CI
- **BND mate 与方向**（deterministic）：优先显式 mate 坐标，也解析四种 VCF ALT 方括号格式；检查 mate 染色体边界；从 ALT 提取两个邻接方向。
  - 分支/约束：可选 mate 无效时 warning 并降级，不使原本可用输入失败
  - 分支/约束：无 mate 时 first-breakend-only
- **保留上游证据**（deterministic）：不解释统计和质量信息，只验证对象形状并原样保留；记录缺失 warning。

实现位置：`agent.py / prompts.py / tools.py`

## 2. 区域注释

查询完整区间、断点窗口和 BND mate 附近的 gene、regulatory、repeat 重叠。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| region_annotation.status | found\|not_found\|error\|blocked | Ensembl 注释阶段总体状态。 | 输入无效时 blocked。 |
| region_annotation.completeness | complete\|partial\|failed | 所有 feature 和断点范围查询的完成程度。 | blocked 时不适用。 |
| region_annotation.query_region / annotation_mode | string | 名义区间和 spatial_overlap_only 模式。 | 有效查询时产生。 |
| region_annotation.features.{gene,regulatory,repeat} | object[]\|null | 名义 SV 区间与三类 Ensembl feature 的重叠；null 表示查询失败，空数组表示成功但无记录。 | 失败时为 null。 |
| region_annotation.breakpoint_annotations.start | object | start CI 或启发式窗口内的 gene/regulatory/repeat、窗口来源和查询状态。 | 有效输入时产生。 |
| region_annotation.breakpoint_annotations.end | object | end CI 或启发式窗口内的 feature 注释。 | 有效输入时产生；可复用 start 查询。 |
| region_annotation.breakpoint_annotations.mate | object\|null | BND mate CI 或启发式窗口内的 feature 注释。 | 无 BND mate 时为 null。 |
| region_annotation.errors / breakpoint errors | object | 按范围和 feature 保存的 HTTP 或响应结构错误。 | 无错误时为空。 |
| region_annotation.truncated | object<boolean> | 每类 feature 是否超过配置上限并被截断。 | 有效查询时产生。 |
| region_annotation.source_urls / retrieved_at | object+datetime | 可追溯的 Ensembl 请求 URL 与检索时间。 | 查询完成时产生。 |
| region_annotation evidence IDs | ENS-prefixed records | 模型从工具原始结果中保留并编号的区域证据。 | 没有可保留记录时为空。 |
| region_annotation.limitations | string\|array | 空间重叠、启发式窗口、截断和未实现注释的限制。 | 必须保留。 |

处理规则：

- **验证状态门**（model-controlled）：validation_error 时返回 blocked，且不调用 Ensembl。
  - 分支/约束：valid → 查询
  - 分支/约束：validation_error → blocked
- **构造注释范围**（deterministic）：完整区间保持原坐标；有 CI 使用绝对 CI；没有 CI 则建立带 heuristic_fallback 标记的 ±tolerance 窗口。
  - 分支/约束：BND 有 mate 时增加独立 mate 范围
- **Ensembl overlap 查询**（external-query）：GRCh37/38 选择对应 Ensembl host；每个范围并行查询 gene、regulatory、repeat；每类最多保留配置上限。
  - 分支/约束：空数组=成功无记录
  - 分支/约束：null=该 feature 查询失败
  - 分支/约束：部分失败=partial
- **组织区域证据**（model-controlled）：明确命名 feature，分配 ENS evidence ID，并原样保留错误、截断、来源和限制。
  - 分支/约束：禁止把空间重叠写成基因破坏、剂量效应或致病性

实现位置：`prompts.py / tools.py:query_ensembl_region`

## 3. 人群数据库

查询 build-matched gnomAD-SV，过滤 SVTYPE，并用确定性规则分类候选相似度。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| database_evidence.status / completeness | status+completeness | gnomAD 查询是否命中，以及多区域请求是否完整完成。 | 输入无效时 blocked。 |
| database_evidence.dataset | gnomad_sv_r4\|gnomad_sv_r2_1 | 根据参考基因组选择的 gnomAD-SV 数据集。 | 有效输入时确定。 |
| database_evidence.query_strategy / query_regions | string+object[] | 完整扩展区间、大型 SV 双窗口或 BND 双 breakend 查询策略及实际区域。 | 有效输入时产生。 |
| database_evidence.breakpoint_windows | object | start、end、mate 的实际检索窗口、来源及是否为测量 CI。 | mate 可为 null。 |
| records[].variant_id/chrom/pos/end/chrom2/pos2/end2 | record coordinates | gnomAD-SV 候选记录标识和一至两个断点坐标。 | 未命中时 records 为空。 |
| records[].type / consequence / length | string+integer\|null | 数据库 SV 类型、数据库 consequence 标签和长度。 | 字段可为空。 |
| records[].ac / an / af / ac_hom / ac_hemi | number\|null | 等位计数、等位总数、频率、纯合和半合计数。 | 数据库未提供时为 null。 |
| records[].filters | string[] | gnomAD-SV 记录的过滤标志。 | 可能为空数组。 |
| records[].match_type | exact\|high_similarity\|partial_overlap\|region_overlap\|nearby | 工具按照固定规则产生的候选匹配类别。 | 不兼容记录被排除。 |
| records[].match_metrics | object | 断点距离、窗口命中、重叠率、长度相似度或 BND 染色体对/双断点指标。 | 随 SVTYPE 使用不同字段。 |
| records[].same_event_established | boolean | 仅在完整所需坐标精确一致时为 true；单端 BND 永不成立。 | 候选记录均产生。 |
| raw/compatible/returned counts + excluded counts + records_truncated | integer+boolean | 原始、兼容、返回、排除和截断数量，用于审计筛选过程。 | 查询结束时产生。 |
| database_evidence.query_errors | object[] | 各 gnomAD 查询区域的网络、GraphQL 或响应结构错误。 | 无错误时为空。 |
| database_evidence evidence IDs | GNO-prefixed records | 模型保留的 gnomAD 候选记录及证据编号。 | 无记录时为空。 |
| source_url / retrieved_at / limitations | provenance | 数据库主页、检索时间和匹配解释限制。 | 必须保留限制。 |

处理规则：

- **选择数据集与查询区域**（deterministic）：GRCh38→gnomad_sv_r4；GRCh37→gnomad_sv_r2_1。≤5 Mb 查询扩展完整区间；大型 SV 查询两个断点；BND 有 mate 时查询两个染色体窗口。
  - 分支/约束：BND 无 mate 保持第一断点检索
- **gnomAD-SV GraphQL 查询**（external-query）：逐区域读取结构变异坐标、类型、频率、基因型计数、consequence 和 filters；按 variant_id 去重。
  - 分支/约束：API 错误不能解释为 not_found
- **普通 SV/INS 候选分类**（deterministic）：先排除不兼容 SVTYPE。DEL/DUP/INV/CNV 计算双断点距离、size similarity 和 reciprocal overlap；INS 比较插入点窗口。
  - 分支/约束：只有完整所需坐标精确一致才设 same_event=true
- **BND 双断点分类**（deterministic）：检查染色体对并允许数据库两端顺序颠倒；计算 local/mate 距离及窗口命中。gnomAD 未返回方向，所以不比较 orientation。
  - 分支/约束：无 mate 时 comparison_scope=first_breakend_only，单端坐标相同也不能建立 same event
- **组织人群证据**（model-controlled）：调用工具一次并保留确定性匹配结果，为保留记录分配 GNO evidence ID；不得用直觉修改 match_type。
  - 分支/约束：其他数据库只能列为 not_queried/tool_not_available

实现位置：`prompts.py / tools.py:query_gnomad_sv`

## 4. 文献检索

根据精确区域、SVTYPE 和 Ensembl 实际返回的基因构造至多三个 PubMed 查询。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| literature_evidence.queries | string[0..3] | 模型根据精确区域/SVTYPE及 Ensembl 实际基因构造的透明 PubMed 查询。 | 验证失败时不构造。 |
| PubMed result.status / query | found\|not_found\|error | 每条 PubMed 检索的状态和原始查询串。 | 每次查询产生。 |
| PubMed records[].pmid/title/authors/source/pubdate/doi/url | citation metadata[] | PubMed PMID 和文献元数据，不包含全文证据。 | 未命中时为空数组。 |
| literature_evidence evidence IDs | PMID-prefixed records | 按 exact-SV、region、gene 或 contextual 分类的文献元数据证据。 | 无记录时为空。 |
| literature_evidence.missing_sources | not_queried records | GO、Reactome、GWAS Catalog 等未实现来源，仅可标为未查询。 | 按需要产生。 |
| literature_evidence.limitations | string[] | 标题/元数据不能支持机制或因果的限制。 | 必须保留。 |

处理规则：

- **构造 PubMed 查询**（model-controlled）：至多三个查询：先精确区域/SVTYPE，再使用 Ensembl 实际返回的基因；不得从模型记忆补基因。
- **PubMed E-utilities**（external-query）：ESearch 获取 PMID，再用 ESummary 获取题名、作者、期刊、日期和 DOI，最多保留配置数量。
  - 分支/约束：无 PMID=not_found
  - 分支/约束：网络/摘要失败=error
- **组织文献上下文**（model-controlled）：区分 exact-SV、region、gene 和 contextual，分配 PMID evidence ID；元数据只作为上下文。
  - 分支/约束：GO/Reactome/GWAS Catalog 标记 not_queried

实现位置：`prompts.py / tools.py:search_pubmed`

## 5. 技术风险

根据质量字段和断点 repeat 注释执行第一轮确定性风险检查。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| artifact_risk.risk_items[low_call_rate] | risk item | call_rate < 0.95 时 present；缺失或非数值时 unknown。 | 始终产生。 |
| artifact_risk.risk_items[single_caller_support] | risk item | 一个 caller 时 present；多个时 absent；缺失时 unknown。 | 始终产生。 |
| artifact_risk.risk_items[repeat_region] | risk item | 根据 start/end 断点窗口 repeat 列表判断 present、absent 或 unknown。 | 查询失败时 unknown。 |
| artifact_risk.risk_items[low_mappability] | risk item | 当前没有 mappability 数据，因此固定为 unknown 并建议外部检查。 | 始终产生。 |
| artifact_risk.risk_items[supporting_reads] | risk item | 支持 reads <= 0 时 present；其他情况当前保持 unknown。 | 始终产生。 |
| artifact_risk.risk_items[genotype_quality] | risk item | 数值 GQ < 20 时 present，>=20 时 absent，否则 unknown。 | 始终产生。 |
| artifact_risk.risk_items[batch_effect] | risk item | batch_checked=false 时 present，true 时 absent，缺失时 unknown。 | 始终产生。 |
| artifact_risk.overall_risk | high\|medium\|low\|unknown | 至少两个 present 为 high；一个 present 为 medium；否则按 unknown/low。 | 解析输入失败时 unknown。 |

处理规则：

- **质量字段规则**（deterministic）：分别检查 call rate、caller 数量、reads、GQ 和 batch_checked；缺失信息保持 unknown；mappability 当前固定 unknown。
- **断点 repeat 风险**（deterministic）：合并 start/end 断点窗口的 repeat 记录；有记录=present；两次成功且均空=absent；任何关键失败=unknown。
  - 分支/约束：当前不使用整个 SV 区间代替断点判断
- **汇总总体风险**（deterministic）：present≥2→high；present=1→medium；无 present 但有 unknown→unknown；全部 absent→low。

实现位置：`prompts.py / tools.py:assess_artifact_risk`

## 6. 证据核验

把候选陈述拆成原子 claim，核验 evidence ID，拒绝无证据事实并记录矛盾。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| verification.publication_allowed | boolean | 保留的报告能否在不包含无证据事实的情况下生成。 | schema 要求。 |
| verification.supported_claims[] | VerifiedClaim[] | 通过证据核验的原子 claim。 | 默认空数组。 |
| verification.rejected_claims[] | VerifiedClaim[] | 证据不足、冲突或过度解释而被拒绝的 claim。 | 默认空数组。 |
| VerifiedClaim.{claim_id,text,claim_type,evidence_ids,confidence,verification_status,notes} | object | 每条原子 claim 的文本、类型、证据链接、置信度和核验状态。 | claim 产生时字段受 schema 约束。 |
| verification.contradictions | string[] | 不同来源或陈述之间的矛盾。 | 默认空数组。 |
| verification.missing_evidence / warnings | string[] | 缺失证据、build/type/match 歧义和核验警告。 | 默认空数组。 |

处理规则：

- **形成原子 claims**（model-structured）：把候选事实和解释拆成 observation、database_fact、inference 或 hypothesis。
  - 分支/约束：不得引入新的科学事实
- **证据链接与核验**（model-structured）：事实 claim 必须引用现有 evidence ID；识别 build/type/match 歧义、矛盾和标题推断。
  - 分支/约束：无证据事实进入 rejected_claims

实现位置：`prompts.py / schemas.py:VerificationOutput`

## 7. 最终报告

只使用前序状态和已核验证据，生成带 evidence catalog 与 provenance 的结构化报告。

| 字段路径 | 类型 | 含义 | 缺失或失败时 |
|---|---|---|---|
| final_report.report_status | complete\|incomplete\|blocked | 输入无效为 blocked；重要来源或质量缺失为 incomplete；否则可为 complete。 | schema 要求。 |
| final_report.sv_summary | SVSummary | 复制标准化坐标、类型、断点 CI、BND mate 和方向等核心候选信息。 | schema 要求。 |
| final_report.{statistical_signals,gene_region_annotation,population_evidence,clinical_phenotype_evidence,literature_evidence,functional_evidence,possible_interpretations} | ReportStatement[] | 按主题组织的陈述，每条包含 evidence_ids、confidence 和 kind。 | 默认空数组。 |
| final_report.artifact_risks | ArtifactRiskItem[] | 技术风险状态、影响、证据链接和推荐检查。 | 默认空数组。 |
| final_report.verified_claims | VerifiedClaim[] | 进入报告的已核验 claim。 | 默认空数组。 |
| final_report.evidence_catalog | EvidenceRecord[] | 所有被引用证据的唯一目录；statement/claim 的 evidence ID 必须存在于此。 | 没有引用时为空。 |
| final_report.query_provenance | ProvenanceItem[] | 每个外部来源的状态、查询摘要和检索时间。 | 默认空数组。 |
| final_report.contradictions / limitations / recommended_next_steps | string[] | 矛盾、系统与证据限制以及可复现的下一步建议。 | 默认空数组。 |
| final_report.report_version | string | 报告结构版本。 | 默认 0.1。 |

处理规则：

- **决定报告状态**（model-structured）：输入无效→blocked；重要来源或质量缺失→incomplete；仅在可审慎发布且必要信息充分时 complete。
- **复制 SV 摘要**（model-structured）：把标准化核心字段复制到 SVSummary，不重新推断坐标、build、类型或 BND mate。
- **组织报告各节**（model-structured）：只使用已提供状态和核验证据，按统计、区域、人群、临床、文献、功能、风险和解释组织内容。
  - 分支/约束：不能恢复 rejected claim
- **证据目录与来源**（model-structured）：复制每个被引用记录的 ID、来源、状态、URL、match type、检索时间和限制。
  - 分支/约束：引用的 evidence ID 必须存在于 catalog 且 catalog ID 唯一
- **结构化报告验证**（schema-validation）：Pydantic 验证 report status、参考基因组、SVTYPE、必需坐标、证据 ID 唯一性及所有内部引用。
  - 分支/约束：validation_error 输入必须对应 blocked 报告

实现位置：`prompts.py / schemas.py:SVReport`

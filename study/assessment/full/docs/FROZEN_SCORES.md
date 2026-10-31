# 既有synthetic proxy of CEO risk preference：版本与边界

回归使用project/data/panel/risk_scores.parquet中的risk_score_ridge和risk_score_xgboost：不带_full的公司—CEO关联分组5折OOF预测，源表29,506行。源行、分折、分组和逐讲话连接信息一起保留。

实际变量为100×max(官方严格匹配接纳的原OOF分数,0)，单位是预测R&D/资产的百分点，不是百分位。两算法分别入模；No actual RD同时不控制实际R&D/资产和其缺失指示变量，With actual RD同时保留两者。

既有第一阶段使用Astra321主题与情绪，以XRD缺失补0后的R&D/资产为目标。资产缺失或不正的行不参与训练。SCORE_METHOD_ORIGINAL.md保留原方法记录，仅作来源说明。总入口不运行训练、主题推断或任何ML模型，requirements不包含XGBoost或sklearn。

官方匹配检查或拒绝源身份及日期证据不足的行，不修复整个上游训练面板，不把分数移给不同CEO或公司。已有分数及其源面板定义是给定输入；本包重新执行财务构建、身份匹配及第二阶段分析。

分数文件保持原始字节，SHA见provenance/immutable_inputs.csv。candidate、vendor和strict分数均复制源OOF值及既有转换，没有重训、调参或依据回归结果重新归一化。

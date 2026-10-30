# Step 4: synthetic proxy of CEO risk preference与分红决策
日期：2026-10-27
本文件仅展示原Excel第3、4页的16个模型。两页均含预测synthetic proxy of CEO risk preference。

## 3. Clipped synthetic proxy of CEO risk preference: without actual R&D/assets

### Xgboost synthetic proxy of CEO risk preference |2013–2023

| Variable | (8) | (9) | (10) | (No debt/Vega) |
|---|---:|---:|---:|---:|
| synthetic proxy of CEO risk preference (clipped at 0, pp) | -0.1915*** (0.0322) | -0.1824*** (0.0482) | -0.2028*** (0.0319) | -0.2043*** (0.0317) |
| CEO cash comp. ($ million) | 0.3427* (0.1806) | 0.1903 (0.2797) | 0.3723** (0.1868) | 0.3985** (0.1854) |
| CEO inside debt ($ million) | 0.0476*** (0.0170) |  |  |  |
| Log CEO relative leverage |  | 0.1513* (0.0772) |  |  |
| High relative leverage dummy |  |  | 1.0522*** (0.3511) |  |
| CEO equity wealth ($ million) | 2.283e-05 (6.455e-05) | 0.0008 (0.0011) | 9.733e-06 (6.876e-05) | -2.160e-05 (3.996e-05) |
| CEO Vega ($ thousand / 1pp vol.) | -0.0002 (0.0004) | 0.0003 (0.0010) | -0.0002 (0.0005) |  |
| CEO age (years) | 0.0155 (0.0180) | 0.0600** (0.0282) | 0.0203 (0.0176) | 0.0208 (0.0180) |
| Log CEO tenure | -0.3566*** (0.1359) | -0.4413** (0.1939) | -0.2959** (0.1333) | -0.2916** (0.1302) |
| CAPEX/assets (pp) | -0.0858*** (0.0304) | -0.1002** (0.0429) | -0.0912*** (0.0311) | -0.0884*** (0.0302) |
| Asset growth (decimal ratio) | -0.4600** (0.2023) | -0.0765 (0.3212) | -0.5193** (0.2112) | -0.5567*** (0.2065) |
| Market/book | 0.0010 (0.0011) | 0.0001 (0.0011) | 0.0012 (0.0011) | 0.0011 (0.0011) |
| Profitability ($ million) | 9.749e-05 (7.788e-05) | 0.0001 (8.922e-05) | 0.0001 (8.087e-05) | 0.0001 (8.504e-05) |
| Size percentile (0-100) | 0.0048 (0.0062) | 0.0185* (0.0099) | 0.0076 (0.0063) | 0.0071 (0.0056) |
| Retained earnings/assets (ratio) | 0.9026*** (0.2487) | 1.4612*** (0.3610) | 0.8196*** (0.2407) | 0.8798*** (0.2430) |
| Return volatility (pp) | -0.9059*** (0.1381) | -0.9379*** (0.1911) | -0.8896*** (0.1372) | -0.9084*** (0.1359) |
| Constant | 2.6181 (1.6521) | 2.1356 (1.8704) | 2.7408** (1.3943) | 3.2278** (1.4799) |
| Industry FE | Yes | Yes | Yes | Yes |
| Year FE | Yes | Yes | Yes | Yes |
| Actual R&D control | No | No | No | No |
| N | 2927 | 1653 | 2927 | 2927 |
| Firm clusters | 591 | 340 | 591 | 591 |
| Log likelihood | -1225.745468 | -625.971007 | -1229.945980 | -1246.013944 |
| Pseudo R2 | 0.393650 | 0.363282 | 0.391572 | 0.383624 |
| Inference | Regular | Regular | Regular | Regular |
| Estimate source | Stata19.5 | Stata19.5 | Stata19.5 | Stata19.5 |
| Stata attempt | success | success | success | success |

### Ridge synthetic proxy of CEO risk preference |2013–2023

| Variable | (8) | (9) | (10) | (No debt/Vega) |
|---|---:|---:|---:|---:|
| synthetic proxy of CEO risk preference (clipped at 0, pp) | -0.1836*** (0.0218) | -0.1890*** (0.0300) | -0.1921*** (0.0215) | -0.1926*** (0.0212) |
| CEO cash comp. ($ million) | 0.3786** (0.1863) | 0.1195 (0.2319) | 0.4173** (0.1953) | 0.4482** (0.1953) |
| CEO inside debt ($ million) | 0.0505*** (0.0179) |  |  |  |
| Log CEO relative leverage |  | 0.1374* (0.0784) |  |  |
| High relative leverage dummy |  |  | 1.0868*** (0.3299) |  |
| CEO equity wealth ($ million) | 2.068e-05 (5.964e-05) | 0.0003 (0.0009) | 6.343e-06 (6.481e-05) | -1.950e-05 (3.971e-05) |
| CEO Vega ($ thousand / 1pp vol.) | -0.0002 (0.0004) | 0.0003 (0.0010) | -0.0001 (0.0004) |  |
| CEO age (years) | 0.0125 (0.0178) | 0.0642** (0.0278) | 0.0173 (0.0176) | 0.0181 (0.0180) |
| Log CEO tenure | -0.3643*** (0.1379) | -0.4267** (0.1951) | -0.3047** (0.1360) | -0.2988** (0.1322) |
| CAPEX/assets (pp) | -0.0910*** (0.0308) | -0.1053** (0.0435) | -0.0969*** (0.0315) | -0.0945*** (0.0307) |
| Asset growth (decimal ratio) | -0.4314** (0.2025) | -0.1221 (0.2932) | -0.4918** (0.2116) | -0.5389** (0.2096) |
| Market/book | 0.0012 (0.0010) | 0.0002 (0.0017) | 0.0013 (0.0010) | 0.0012 (0.0009) |
| Profitability ($ million) | 0.0001 (6.748e-05) | 0.0001 (8.355e-05) | 0.0001* (7.265e-05) | 0.0001 (7.773e-05) |
| Size percentile (0-100) | 0.0046 (0.0059) | 0.0209** (0.0097) | 0.0077 (0.0061) | 0.0074 (0.0055) |
| Retained earnings/assets (ratio) | 0.9497*** (0.2551) | 1.5558*** (0.3569) | 0.8689*** (0.2496) | 0.9348*** (0.2491) |
| Return volatility (pp) | -0.9412*** (0.1392) | -0.9576*** (0.1879) | -0.9208*** (0.1359) | -0.9397*** (0.1347) |
| Constant | 3.0386* (1.6658) | 2.1316 (1.8456) | 3.2222** (1.3934) | 3.7321** (1.4732) |
| Industry FE | Yes | Yes | Yes | Yes |
| Year FE | Yes | Yes | Yes | Yes |
| Actual R&D control | No | No | No | No |
| N | 2927 | 1653 | 2927 | 2927 |
| Firm clusters | 591 | 340 | 591 | 591 |
| Log likelihood | -1212.032041 | -615.496621 | -1217.384874 | -1234.315221 |
| Pseudo R2 | 0.400434 | 0.373936 | 0.397786 | 0.389411 |
| Inference | Regular | Regular | Regular | Regular |
| Estimate source | Stata19.5 | Stata19.5 | Stata19.5 | Stata19.5 |
| Stata attempt | success | success | success | success |


## 4. Clipped synthetic proxy of CEO risk preference: with actual R&D/assets

### Xgboost synthetic proxy of CEO risk preference |2013–2023

| Variable | (8) | (9) | (10) | (No debt/Vega) |
|---|---:|---:|---:|---:|
| synthetic proxy of CEO risk preference (clipped at 0, pp) | -0.1423*** (0.0347) | -0.1501*** (0.0502) | -0.1516*** (0.0342) | -0.1545*** (0.0341) |
| CEO cash comp. ($ million) | 0.3118* (0.1746) | 0.1569 (0.2531) | 0.3405* (0.1811) | 0.3616** (0.1780) |
| CEO inside debt ($ million) | 0.0477*** (0.0168) |  |  |  |
| Log CEO relative leverage |  | 0.1575** (0.0777) |  |  |
| High relative leverage dummy |  |  | 1.0399*** (0.3490) |  |
| CEO equity wealth ($ million) | 2.425e-05 (6.473e-05) | 0.0008 (0.0011) | 1.065e-05 (6.962e-05) | -2.894e-05 (7.217e-05) |
| CEO Vega ($ thousand / 1pp vol.) | -0.0003 (0.0004) | 0.0002 (0.0010) | -0.0002 (0.0005) |  |
| CEO age (years) | 0.0145 (0.0183) | 0.0592** (0.0281) | 0.0196 (0.0180) | 0.0200 (0.0184) |
| Log CEO tenure | -0.3383** (0.1385) | -0.4211** (0.1958) | -0.2727** (0.1354) | -0.2700** (0.1321) |
| Actual R&D/assets (pp) | -0.0792** (0.0378) | -0.0612 (0.0457) | -0.0875** (0.0384) | -0.0831** (0.0382) |
| R&D missing dummy | 0.4122 (0.3063) | 0.1722 (0.4592) | 0.3157 (0.3068) | 0.3485 (0.3068) |
| CAPEX/assets (pp) | -0.0868*** (0.0302) | -0.1003** (0.0434) | -0.0921*** (0.0309) | -0.0895*** (0.0301) |
| Asset growth (decimal ratio) | -0.5106** (0.2013) | -0.1050 (0.3184) | -0.5746*** (0.2111) | -0.6072*** (0.2071) |
| Market/book | 0.0012 (0.0011) | 0.0002 (0.0017) | 0.0014 (0.0011) | 0.0012 (0.0010) |
| Profitability ($ million) | 9.786e-05 (7.422e-05) | 0.0001 (8.864e-05) | 0.0001 (7.861e-05) | 0.0001 (8.438e-05) |
| Size percentile (0-100) | 0.0053 (0.0062) | 0.0197** (0.0099) | 0.0081 (0.0064) | 0.0075 (0.0057) |
| Retained earnings/assets (ratio) | 0.8594*** (0.2566) | 1.4899*** (0.3689) | 0.7723*** (0.2468) | 0.8384*** (0.2529) |
| Return volatility (pp) | -0.9038*** (0.1385) | -0.9269*** (0.1898) | -0.8870*** (0.1382) | -0.9062*** (0.1367) |
| Constant | 2.2109 (1.6776) | 1.9292 (1.9333) | 2.4144* (1.4525) | 2.8887* (1.5301) |
| Industry FE | Yes | Yes | Yes | Yes |
| Year FE | Yes | Yes | Yes | Yes |
| Actual R&D control | Yes | Yes | Yes | Yes |
| N | 2927 | 1653 | 2927 | 2927 |
| Firm clusters | 591 | 340 | 591 | 591 |
| Log likelihood | -1212.367015 | -623.480305 | -1217.045168 | -1232.990350 |
| Pseudo R2 | 0.400268 | 0.365816 | 0.397954 | 0.390067 |
| Inference | Regular | Regular | Regular | Regular |
| Estimate source | Stata19.5 | Stata19.5 | Stata19.5 | Stata19.5 |
| Stata attempt | success | success | success | success |

### Ridge synthetic proxy of CEO risk preference |2013–2023

| Variable | (8) | (9) | (10) | (No debt/Vega) |
|---|---:|---:|---:|---:|
| synthetic proxy of CEO risk preference (clipped at 0, pp) | -0.1478*** (0.0241) | -0.1680*** (0.0317) | -0.1532*** (0.0236) | -0.1542*** (0.0235) |
| CEO cash comp. ($ million) | 0.3333* (0.1789) | 0.1015 (0.2175) | 0.3668* (0.1881) | 0.3917** (0.1865) |
| CEO inside debt ($ million) | 0.0495*** (0.0173) |  |  |  |
| Log CEO relative leverage |  | 0.1444* (0.0789) |  |  |
| High relative leverage dummy |  |  | 1.0677*** (0.3330) |  |
| CEO equity wealth ($ million) | 2.320e-05 (6.163e-05) | 0.0004 (0.0009) | 8.077e-06 (6.801e-05) | -2.527e-05 (5.827e-05) |
| CEO Vega ($ thousand / 1pp vol.) | -0.0003 (0.0004) | 0.0003 (0.0010) | -0.0002 (0.0004) |  |
| CEO age (years) | 0.0127 (0.0183) | 0.0637** (0.0278) | 0.0176 (0.0181) | 0.0182 (0.0184) |
| Log CEO tenure | -0.3436** (0.1397) | -0.4117** (0.1967) | -0.2783** (0.1374) | -0.2742** (0.1336) |
| Actual R&D/assets (pp) | -0.0757** (0.0369) | -0.0512 (0.0450) | -0.0869** (0.0378) | -0.0836** (0.0382) |
| R&D missing dummy | 0.4424 (0.3073) | 0.1522 (0.4712) | 0.3364 (0.3077) | 0.3710 (0.3084) |
| CAPEX/assets (pp) | -0.0917*** (0.0306) | -0.1044** (0.0439) | -0.0974*** (0.0312) | -0.0951*** (0.0306) |
| Asset growth (decimal ratio) | -0.4816** (0.2010) | -0.1399 (0.2970) | -0.5465*** (0.2113) | -0.5879*** (0.2089) |
| Market/book | 0.0014 (0.0010) | 0.0003 (0.0017) | 0.0015 (0.0009) | 0.0014 (0.0009) |
| Profitability ($ million) | 0.0001 (6.628e-05) | 0.0001 (8.356e-05) | 0.0001* (7.168e-05) | 0.0001 (7.834e-05) |
| Size percentile (0-100) | 0.0053 (0.0060) | 0.0217** (0.0097) | 0.0083 (0.0062) | 0.0079 (0.0057) |
| Retained earnings/assets (ratio) | 0.8905*** (0.2637) | 1.5736*** (0.3625) | 0.8045*** (0.2559) | 0.8724*** (0.2604) |
| Return volatility (pp) | -0.9314*** (0.1392) | -0.9426*** (0.1862) | -0.9108*** (0.1373) | -0.9299*** (0.1358) |
| Constant | 2.5001 (1.6856) | 1.8972 (1.9284) | 2.7536* (1.4571) | 3.2391** (1.5342) |
| Industry FE | Yes | Yes | Yes | Yes |
| Year FE | Yes | Yes | Yes | Yes |
| Actual R&D control | Yes | Yes | Yes | Yes |
| N | 2927 | 1653 | 2927 | 2927 |
| Firm clusters | 591 | 340 | 591 | 591 |
| Log likelihood | -1197.588928 | -613.538074 | -1202.873275 | -1219.402791 |
| Pseudo R2 | 0.407579 | 0.375928 | 0.404965 | 0.396788 |
| Inference | Regular | Regular | Regular | Regular |
| Estimate source | Stata19.5 | Stata19.5 | Stata19.5 | Stata19.5 |
| Stata attempt | success | success | success | success |

## Notes

- Annual CEO B; fiscal years 2013-2023; Ridge and XGBoost enter separately.
- Score = 100 * max(frozen out-of-fold predicted R&D/assets, 0); no _full predictions.
- Pooled Logit with constant, separate SIC2 and fiscal-year dummies. Parentheses: GVKEY firm-cluster SE, CR0*G/(G-1); normal two-sided Wald stars: *** p<.01, ** p<.05, * p<.10.
- No actual RD excludes both rd_at_pct and rd_missing; With actual RD includes both. Delta/Vega is excluded from all16 models.
- m00 is an added setting with cash compensation and equity wealth but no inside-debt proxy or Vega. The original annual-B eligibility requirements remain in force.
- Coefficients/SE/stars: frozen Stata 19.5 results; LL/pseudo-R2 footer: frozen Python full-design MLE.

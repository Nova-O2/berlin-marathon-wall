| term                                         |    coef |     OR |   OR_CI_lo |   OR_CI_hi |      p | model       |      n |         AIC | subset   |
|:---------------------------------------------|--------:|-------:|-----------:|-----------:|-------:|:------------|-------:|------------:|:---------|
| Intercept                                    | -1.0617 | 0.3459 |     0.3358 |     0.3562 | 0.0000 | main        | 855061 | 623955.3220 | Full     |
| C(gender_label)[T.Male]                      |  1.3552 | 3.8774 |     3.8118 |     3.9442 | 0.0000 | main        | 855061 | 623955.3220 | Full     |
| C(performance_category)[T.Recreational]      | -1.2224 | 0.2945 |     0.2900 |     0.2991 | 0.0000 | main        | 855061 | 623955.3220 | Full     |
| C(performance_category)[T.Intermediate]      | -2.2038 | 0.1104 |     0.1083 |     0.1125 | 0.0000 | main        | 855061 | 623955.3220 | Full     |
| C(performance_category)[T.Advanced]          | -2.8088 | 0.0603 |     0.0585 |     0.0621 | 0.0000 | main        | 855061 | 623955.3220 | Full     |
| C(performance_category)[T.Competitive (<3h)] | -4.1057 | 0.0165 |     0.0151 |     0.0180 | 0.0000 | main        | 855061 | 623955.3220 | Full     |
| age_mid                                      | -0.0134 | 0.9867 |     0.9861 |     0.9873 | 0.0000 | main        | 855061 | 623955.3220 | Full     |
| Intercept                                    | -1.3167 | 0.2680 |     0.2515 |     0.2856 | 0.0000 | interaction | 855061 | 623877.8847 | Full     |
| C(gender_label)[T.Male]                      |  1.6633 | 5.2767 |     4.9197 |     5.6596 | 0.0000 | interaction | 855061 | 623877.8847 | Full     |
| C(performance_category)[T.Recreational]      | -1.2234 | 0.2942 |     0.2897 |     0.2988 | 0.0000 | interaction | 855061 | 623877.8847 | Full     |
| C(performance_category)[T.Intermediate]      | -2.2063 | 0.1101 |     0.1081 |     0.1122 | 0.0000 | interaction | 855061 | 623877.8847 | Full     |
| C(performance_category)[T.Advanced]          | -2.8131 | 0.0600 |     0.0583 |     0.0618 | 0.0000 | interaction | 855061 | 623877.8847 | Full     |
| C(performance_category)[T.Competitive (<3h)] | -4.1131 | 0.0164 |     0.0150 |     0.0178 | 0.0000 | interaction | 855061 | 623877.8847 | Full     |
| age_mid                                      | -0.0072 | 0.9928 |     0.9914 |     0.9943 | 0.0000 | interaction | 855061 | 623877.8847 | Full     |
| C(gender_label)[T.Male]:age_mid              | -0.0074 | 0.9926 |     0.9910 |     0.9943 | 0.0000 | interaction | 855061 | 623877.8847 | Full     |
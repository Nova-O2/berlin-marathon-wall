| term                                         |    coef |     OR |   OR_CI_lo |   OR_CI_hi |      p | model       |      n |         AIC | subset   |
|:---------------------------------------------|--------:|-------:|-----------:|-----------:|-------:|:------------|-------:|------------:|:---------|
| Intercept                                    | -1.0876 | 0.3370 |     0.3263 |     0.3482 | 0.0000 | main        | 684026 | 497372.8909 | Dedup    |
| C(gender_label)[T.Male]                      |  1.3407 | 3.8216 |     3.7515 |     3.8931 | 0.0000 | main        | 684026 | 497372.8909 | Dedup    |
| C(performance_category)[T.Recreational]      | -1.2352 | 0.2908 |     0.2858 |     0.2959 | 0.0000 | main        | 684026 | 497372.8909 | Dedup    |
| C(performance_category)[T.Intermediate]      | -2.1800 | 0.1130 |     0.1107 |     0.1155 | 0.0000 | main        | 684026 | 497372.8909 | Dedup    |
| C(performance_category)[T.Advanced]          | -2.7375 | 0.0647 |     0.0626 |     0.0669 | 0.0000 | main        | 684026 | 497372.8909 | Dedup    |
| C(performance_category)[T.Competitive (<3h)] | -4.0048 | 0.0182 |     0.0166 |     0.0200 | 0.0000 | main        | 684026 | 497372.8909 | Dedup    |
| age_mid                                      | -0.0130 | 0.9871 |     0.9864 |     0.9877 | 0.0000 | main        | 684026 | 497372.8909 | Dedup    |
| Intercept                                    | -1.3037 | 0.2715 |     0.2537 |     0.2906 | 0.0000 | interaction | 684026 | 497324.0309 | Dedup    |
| C(gender_label)[T.Male]                      |  1.6061 | 4.9832 |     4.6212 |     5.3735 | 0.0000 | interaction | 684026 | 497324.0309 | Dedup    |
| C(performance_category)[T.Recreational]      | -1.2360 | 0.2905 |     0.2855 |     0.2956 | 0.0000 | interaction | 684026 | 497324.0309 | Dedup    |
| C(performance_category)[T.Intermediate]      | -2.1820 | 0.1128 |     0.1104 |     0.1152 | 0.0000 | interaction | 684026 | 497324.0309 | Dedup    |
| C(performance_category)[T.Advanced]          | -2.7410 | 0.0645 |     0.0624 |     0.0667 | 0.0000 | interaction | 684026 | 497324.0309 | Dedup    |
| C(performance_category)[T.Competitive (<3h)] | -4.0111 | 0.0181 |     0.0165 |     0.0199 | 0.0000 | interaction | 684026 | 497324.0309 | Dedup    |
| age_mid                                      | -0.0077 | 0.9923 |     0.9907 |     0.9939 | 0.0000 | interaction | 684026 | 497324.0309 | Dedup    |
| C(gender_label)[T.Male]:age_mid              | -0.0064 | 0.9936 |     0.9919 |     0.9954 | 0.0000 | interaction | 684026 | 497324.0309 | Dedup    |
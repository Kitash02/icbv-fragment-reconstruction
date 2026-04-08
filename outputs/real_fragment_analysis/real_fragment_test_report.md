# Real Fragment Test Report

Generated: 2026-04-08 10:47:11

## Executive Summary

- **Fragments Tested**: 46
- **Preprocessing Success Rate**: 69.6%
- **Positive Pairs Tested**: 3
- **Negative Pairs Tested**: 1
- **Overall Accuracy**: 75.0%

## Preprocessing Results

- Successfully preprocessed: 32/46
- Failed: 14/46
- Success rate: **69.6%**

### Preprocessing Failures

| Fragment | Source | Error |
|----------|--------|-------|
| candidate_11_Pottery_sherd_-_YDEA_-_91292 | wikimedia | Could not load image: data\raw\real_fragments_validated\wikimedia\candidate_11_Pottery_sherd_-_YDEA_-_91292.jpg |
| candidate_12_Pottery_sherd_-_YDEA_-_91299 | wikimedia | Could not load image: data\raw\real_fragments_validated\wikimedia\candidate_12_Pottery_sherd_-_YDEA_-_91299.jpg |
| candidate_13_Pottery_sherd_-_YDEA_-_91290 | wikimedia | Could not load image: data\raw\real_fragments_validated\wikimedia\candidate_13_Pottery_sherd_-_YDEA_-_91290.jpg |
| candidate_14_Pottery_sherd_-_YDEA_-_91306 | wikimedia | Could not load image: data\raw\real_fragments_validated\wikimedia\candidate_14_Pottery_sherd_-_YDEA_-_91306.jpg |
| candidate_15_Pottery_sherd_-_YDEA_-_91303 | wikimedia | Could not load image: data\raw\real_fragments_validated\wikimedia\candidate_15_Pottery_sherd_-_YDEA_-_91303.jpg |
| candidate_16_02024_0849_Identifying_pottery_sherds | wikimedia | Could not load image: data\raw\real_fragments_validated\wikimedia\candidate_16_02024_0849_Identifying_pottery_sherds.jpg |
| candidate_17_02024_0861_Identifying_pottery_sherds | wikimedia | Could not load image: data\raw\real_fragments_validated\wikimedia\candidate_17_02024_0861_Identifying_pottery_sherds.jpg |
| candidate_18_02024_0867_Identifying_pottery_sherds | wikimedia | Could not load image: data\raw\real_fragments_validated\wikimedia\candidate_18_02024_0867_Identifying_pottery_sherds.jpg |
| candidate_19_Pottery_Sherd__Never_remove_artifacts-_replace_all_objects_exactly_where_you_discovered_them.___14368025114_ | wikimedia | Could not load image: data\raw\real_fragments_validated\wikimedia\candidate_19_Pottery_Sherd__Never_remove_artifacts-_replace_all_objects_exactly_where_you_discovered_them.___14368025114_.jpg |
| candidate_20_Pottery_Sherd__Never_remove_artifacts-_replace_all_objects_exactly_where_you_discovered_them.___14368922545_ | wikimedia | Could not load image: data\raw\real_fragments_validated\wikimedia\candidate_20_Pottery_Sherd__Never_remove_artifacts-_replace_all_objects_exactly_where_you_discovered_them.___14368922545_.jpg |
| candidate_3_Pottery_sherd_-_YDEA_-_91288 | wikimedia | Could not load image: data\raw\real_fragments_validated\wikimedia\candidate_3_Pottery_sherd_-_YDEA_-_91288.jpg |
| candidate_5_Pottery_sherd_-_YDEA_-_91301 | wikimedia | Could not load image: data\raw\real_fragments_validated\wikimedia\candidate_5_Pottery_sherd_-_YDEA_-_91301.jpg |
| candidate_7_Pottery_sherd_-_YDEA_-_91286 | wikimedia | Could not load image: data\raw\real_fragments_validated\wikimedia\candidate_7_Pottery_sherd_-_YDEA_-_91286.jpg |
| candidate_9_Pottery_sherd_-_YDEA_-_91307 | wikimedia | Could not load image: data\raw\real_fragments_validated\wikimedia\candidate_9_Pottery_sherd_-_YDEA_-_91307.jpg |

## Matching Results

### Positive Cases (Same Source)

- Correct matches: 3/3
- Incorrect rejections: 0/3
- Accuracy: **100.0%**
- Average confidence: 0.256

### Negative Cases (Different Sources)

- Correct rejections: 0/1
- False positives: 1/1
- Accuracy: **0.0%**
- Average confidence: 0.260

### Detailed Pair Results

| Fragment A | Fragment B | Type | Verdict | Confidence | Color BC | Correct? |
|------------|------------|------|---------|------------|----------|----------|
| 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_001 | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_002 | SAME | MATCH | 0.258 | 0.836 | YES |
| 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_002 | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_003 | SAME | MATCH | 0.254 | 0.927 | YES |
| 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_003 | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_004 | SAME | MATCH | 0.254 | 0.946 | YES |
| candidate_10_Pottery_sherd_-_YDEA_-_91293 | 14_scherven_-_O36ZFL_-_60015859_-_RCE_fragment_001 | DIFF | MATCH | 0.260 | 0.820 | NO |

## Insights and Recommendations

- **Preprocessing Issues**: Success rate is below 80%. Consider:
  - Improving image quality (lighting, resolution)
  - Adjusting preprocessing parameters (Canny thresholds, morphological operations)
  - Using more consistent background removal

- **False Positive Issues**: Negative accuracy is low. Fragments from different sources are being incorrectly matched.
  - Consider tightening matching thresholds
  - Improve color-based filtering (currently uses Bhattacharyya coefficient)
  - Add additional appearance-based features

---

*Note: This report compares real archaeological fragment performance against benchmark (synthetic) data. Differences are expected due to real-world challenges like uneven lighting, surface damage, and irregular backgrounds.*

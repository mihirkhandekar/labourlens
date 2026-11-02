# Second-family judge: sonnet55-FIN-s60-b-20261102

Status: **complete**. Judge: `claude-sonnet-5-5` versus `gpt-6.1-terra`. Completed 240/240 items (58 cached attempts, 5 semantic retries). New list-price spend $0.767506; budget accounting including uncertain attempts $0.767506, cap $4.00.

See summary.json for agreement, paired differences, problem flags and family disagreements; labels.json contains labels only. No human review; one saved generation run, conditional paired answered sample; costs are token-based estimates, not invoices. Aborted runs have no inferential analysis.

```json
{
  "agreement": {
    "claim_labels": {
      "n": 432,
      "raw_agreement": 0.8425925925925926,
      "kappa": 0.43603133159268914
    },
    "any_unsupported": {
      "n": 234,
      "raw_agreement": 0.9957264957264957,
      "kappa": 0.0
    },
    "any_contradicted": {
      "n": 226,
      "raw_agreement": 0.995575221238938,
      "kappa": 0.9068425391591094
    }
  },
  "arm_rates": {
    "gpt-5.6-luna/all": {
      "r3": {
        "original": {
          "claim_support": {
            "positive": 99,
            "total": 114,
            "rate": 0.868421052631579
          },
          "fact_coverage": {
            "positive": 77,
            "total": 96,
            "rate": 0.8020833333333334
          }
        },
        "second": {
          "claim_support": {
            "positive": 98,
            "total": 114,
            "rate": 0.8596491228070176
          },
          "fact_coverage": {
            "positive": 82,
            "total": 96,
            "rate": 0.8541666666666666
          }
        }
      },
      "hybrid": {
        "original": {
          "claim_support": {
            "positive": 82,
            "total": 117,
            "rate": 0.7008547008547008
          },
          "fact_coverage": {
            "positive": 73,
            "total": 96,
            "rate": 0.7604166666666666
          }
        },
        "second": {
          "claim_support": {
            "positive": 100,
            "total": 117,
            "rate": 0.8547008547008547
          },
          "fact_coverage": {
            "positive": 78,
            "total": 96,
            "rate": 0.8125
          }
        }
      }
    },
    "gpt-5.6-luna/dev": {
      "r3": {
        "original": {
          "claim_support": {
            "positive": 78,
            "total": 92,
            "rate": 0.8478260869565217
          },
          "fact_coverage": {
            "positive": 59,
            "total": 75,
            "rate": 0.7866666666666666
          }
        },
        "second": {
          "claim_support": {
            "positive": 76,
            "total": 92,
            "rate": 0.8260869565217391
          },
          "fact_coverage": {
            "positive": 63,
            "total": 75,
            "rate": 0.84
          }
        }
      },
      "hybrid": {
        "original": {
          "claim_support": {
            "positive": 65,
            "total": 95,
            "rate": 0.6842105263157895
          },
          "fact_coverage": {
            "positive": 58,
            "total": 75,
            "rate": 0.7733333333333333
          }
        },
        "second": {
          "claim_support": {
            "positive": 81,
            "total": 95,
            "rate": 0.8526315789473684
          },
          "fact_coverage": {
            "positive": 62,
            "total": 75,
            "rate": 0.8266666666666667
          }
        }
      }
    },
    "gpt-5.6-luna/heldout": {
      "r3": {
        "original": {
          "claim_support": {
            "positive": 10,
            "total": 11,
            "rate": 0.9090909090909091
          },
          "fact_coverage": {
            "positive": 7,
            "total": 7,
            "rate": 1.0
          }
        },
        "second": {
          "claim_support": {
            "positive": 11,
            "total": 11,
            "rate": 1.0
          },
          "fact_coverage": {
            "positive": 7,
            "total": 7,
            "rate": 1.0
          }
        }
      },
      "hybrid": {
        "original": {
          "claim_support": {
            "positive": 6,
            "total": 11,
            "rate": 0.5454545454545454
          },
          "fact_coverage": {
            "positive": 5,
            "total": 7,
            "rate": 0.7142857142857143
          }
        },
        "second": {
          "claim_support": {
            "positive": 8,
            "total": 11,
            "rate": 0.7272727272727273
          },
          "fact_coverage": {
            "positive": 5,
            "total": 7,
            "rate": 0.7142857142857143
          }
        }
      }
    },
    "gpt-5.6-luna/fresh": {
      "r3": {
        "original": {
          "claim_support": {
            "positive": 11,
            "total": 11,
            "rate": 1.0
          },
          "fact_coverage": {
            "positive": 11,
            "total": 14,
            "rate": 0.7857142857142857
          }
        },
        "second": {
          "claim_support": {
            "positive": 11,
            "total": 11,
            "rate": 1.0
          },
          "fact_coverage": {
            "positive": 12,
            "total": 14,
            "rate": 0.8571428571428571
          }
        }
      },
      "hybrid": {
        "original": {
          "claim_support": {
            "positive": 11,
            "total": 11,
            "rate": 1.0
          },
          "fact_coverage": {
            "positive": 10,
            "total": 14,
            "rate": 0.7142857142857143
          }
        },
        "second": {
          "claim_support": {
            "positive": 11,
            "total": 11,
            "rate": 1.0
          },
          "fact_coverage": {
            "positive": 11,
            "total": 14,
            "rate": 0.7857142857142857
          }
        }
      }
    },
    "gpt-6-luna/all": {
      "r3": {
        "original": {
          "claim_support": {
            "positive": 83,
            "total": 100,
            "rate": 0.83
          },
          "fact_coverage": {
            "positive": 68,
            "total": 94,
            "rate": 0.723404255319149
          }
        },
        "second": {
          "claim_support": {
            "positive": 88,
            "total": 100,
            "rate": 0.88
          },
          "fact_coverage": {
            "positive": 78,
            "total": 94,
            "rate": 0.8297872340425532
          }
        }
      },
      "hybrid": {
        "original": {
          "claim_support": {
            "positive": 81,
            "total": 101,
            "rate": 0.801980198019802
          },
          "fact_coverage": {
            "positive": 64,
            "total": 94,
            "rate": 0.6808510638297872
          }
        },
        "second": {
          "claim_support": {
            "positive": 90,
            "total": 101,
            "rate": 0.8910891089108911
          },
          "fact_coverage": {
            "positive": 74,
            "total": 94,
            "rate": 0.7872340425531915
          }
        }
      }
    },
    "gpt-6-luna/dev": {
      "r3": {
        "original": {
          "claim_support": {
            "positive": 59,
            "total": 76,
            "rate": 0.7763157894736842
          },
          "fact_coverage": {
            "positive": 54,
            "total": 72,
            "rate": 0.75
          }
        },
        "second": {
          "claim_support": {
            "positive": 67,
            "total": 76,
            "rate": 0.881578947368421
          },
          "fact_coverage": {
            "positive": 60,
            "total": 72,
            "rate": 0.8333333333333334
          }
        }
      },
      "hybrid": {
        "original": {
          "claim_support": {
            "positive": 60,
            "total": 77,
            "rate": 0.7792207792207793
          },
          "fact_coverage": {
            "positive": 49,
            "total": 72,
            "rate": 0.6805555555555556
          }
        },
        "second": {
          "claim_support": {
            "positive": 69,
            "total": 77,
            "rate": 0.8961038961038961
          },
          "fact_coverage": {
            "positive": 55,
            "total": 72,
            "rate": 0.7638888888888888
          }
        }
      }
    },
    "gpt-6-luna/heldout": {
      "r3": {
        "original": {
          "claim_support": {
            "positive": 11,
            "total": 11,
            "rate": 1.0
          },
          "fact_coverage": {
            "positive": 5,
            "total": 8,
            "rate": 0.625
          }
        },
        "second": {
          "claim_support": {
            "positive": 9,
            "total": 11,
            "rate": 0.8181818181818182
          },
          "fact_coverage": {
            "positive": 7,
            "total": 8,
            "rate": 0.875
          }
        }
      },
      "hybrid": {
        "original": {
          "claim_support": {
            "positive": 8,
            "total": 11,
            "rate": 0.7272727272727273
          },
          "fact_coverage": {
            "positive": 5,
            "total": 8,
            "rate": 0.625
          }
        },
        "second": {
          "claim_support": {
            "positive": 9,
            "total": 11,
            "rate": 0.8181818181818182
          },
          "fact_coverage": {
            "positive": 7,
            "total": 8,
            "rate": 0.875
          }
        }
      }
    },
    "gpt-6-luna/fresh": {
      "r3": {
        "original": {
          "claim_support": {
            "positive": 13,
            "total": 13,
            "rate": 1.0
          },
          "fact_coverage": {
            "positive": 9,
            "total": 14,
            "rate": 0.6428571428571429
          }
        },
        "second": {
          "claim_support": {
            "positive": 12,
            "total": 13,
            "rate": 0.9230769230769231
          },
          "fact_coverage": {
            "positive": 11,
            "total": 14,
            "rate": 0.7857142857142857
          }
        }
      },
      "hybrid": {
        "original": {
          "claim_support": {
            "positive": 13,
            "total": 13,
            "rate": 1.0
          },
          "fact_coverage": {
            "positive": 10,
            "total": 14,
            "rate": 0.7142857142857143
          }
        },
        "second": {
          "claim_support": {
            "positive": 12,
            "total": 13,
            "rate": 0.9230769230769231
          },
          "fact_coverage": {
            "positive": 12,
            "total": 14,
            "rate": 0.8571428571428571
          }
        }
      }
    }
  },
  "paired": {
    "gpt-5.6-luna": {
      "all": {
        "claim_support": {
          "judges": {
            "original": {
              "pooled_r3_minus_hybrid": 0.16756635177687818,
              "mean_paired_r3_minus_hybrid": 0.10517241379310344,
              "n_pairs": 58
            },
            "second": {
              "pooled_r3_minus_hybrid": 0.00494826810616289,
              "mean_paired_r3_minus_hybrid": -0.001436781609195402,
              "n_pairs": 58
            }
          },
          "sign_flip": {
            "pooled_r3_minus_hybrid": false,
            "mean_paired_r3_minus_hybrid": true
          }
        },
        "fact_coverage": {
          "judges": {
            "original": {
              "pooled_r3_minus_hybrid": 0.04166666666666674,
              "mean_paired_r3_minus_hybrid": 0.03273809523809524,
              "n_pairs": 56
            },
            "second": {
              "pooled_r3_minus_hybrid": 0.04166666666666663,
              "mean_paired_r3_minus_hybrid": 0.04017857142857143,
              "n_pairs": 56
            }
          },
          "sign_flip": {
            "pooled_r3_minus_hybrid": false,
            "mean_paired_r3_minus_hybrid": false
          }
        }
      },
      "dev": {
        "claim_support": {
          "judges": {
            "original": {
              "pooled_r3_minus_hybrid": 0.16361556064073224,
              "mean_paired_r3_minus_hybrid": 0.10643939393939394,
              "n_pairs": 44
            },
            "second": {
              "pooled_r3_minus_hybrid": -0.026544622425629272,
              "mean_paired_r3_minus_hybrid": -0.024621212121212124,
              "n_pairs": 44
            }
          },
          "sign_flip": {
            "pooled_r3_minus_hybrid": true,
            "mean_paired_r3_minus_hybrid": true
          }
        },
        "fact_coverage": {
          "judges": {
            "original": {
              "pooled_r3_minus_hybrid": 0.013333333333333308,
              "mean_paired_r3_minus_hybrid": 0.005952380952380952,
              "n_pairs": 42
            },
            "second": {
              "pooled_r3_minus_hybrid": 0.013333333333333308,
              "mean_paired_r3_minus_hybrid": 0.015873015873015872,
              "n_pairs": 42
            }
          },
          "sign_flip": {
            "pooled_r3_minus_hybrid": false,
            "mean_paired_r3_minus_hybrid": false
          }
        }
      },
      "heldout": {
        "claim_support": {
          "judges": {
            "original": {
              "pooled_r3_minus_hybrid": 0.36363636363636365,
              "mean_paired_r3_minus_hybrid": 0.2833333333333333,
              "n_pairs": 5
            },
            "second": {
              "pooled_r3_minus_hybrid": 0.2727272727272727,
              "mean_paired_r3_minus_hybrid": 0.2,
              "n_pairs": 5
            }
          },
          "sign_flip": {
            "pooled_r3_minus_hybrid": false,
            "mean_paired_r3_minus_hybrid": false
          }
        },
        "fact_coverage": {
          "judges": {
            "original": {
              "pooled_r3_minus_hybrid": 0.2857142857142857,
              "mean_paired_r3_minus_hybrid": 0.2666666666666667,
              "n_pairs": 5
            },
            "second": {
              "pooled_r3_minus_hybrid": 0.2857142857142857,
              "mean_paired_r3_minus_hybrid": 0.2666666666666667,
              "n_pairs": 5
            }
          },
          "sign_flip": {
            "pooled_r3_minus_hybrid": false,
            "mean_paired_r3_minus_hybrid": false
          }
        }
      },
      "fresh": {
        "claim_support": {
          "judges": {
            "original": {
              "pooled_r3_minus_hybrid": 0.0,
              "mean_paired_r3_minus_hybrid": 0.0,
              "n_pairs": 9
            },
            "second": {
              "pooled_r3_minus_hybrid": 0.0,
              "mean_paired_r3_minus_hybrid": 0.0,
              "n_pairs": 9
            }
          },
          "sign_flip": {
            "pooled_r3_minus_hybrid": false,
            "mean_paired_r3_minus_hybrid": false
          }
        },
        "fact_coverage": {
          "judges": {
            "original": {
              "pooled_r3_minus_hybrid": 0.0714285714285714,
              "mean_paired_r3_minus_hybrid": 0.027777777777777776,
              "n_pairs": 9
            },
            "second": {
              "pooled_r3_minus_hybrid": 0.0714285714285714,
              "mean_paired_r3_minus_hybrid": 0.027777777777777776,
              "n_pairs": 9
            }
          },
          "sign_flip": {
            "pooled_r3_minus_hybrid": false,
            "mean_paired_r3_minus_hybrid": false
          }
        }
      }
    },
    "gpt-6-luna": {
      "all": {
        "claim_support": {
          "judges": {
            "original": {
              "pooled_r3_minus_hybrid": 0.028019801980197934,
              "mean_paired_r3_minus_hybrid": -0.010451977401129943,
              "n_pairs": 59
            },
            "second": {
              "pooled_r3_minus_hybrid": -0.011089108910891099,
              "mean_paired_r3_minus_hybrid": -0.03474576271186441,
              "n_pairs": 59
            }
          },
          "sign_flip": {
            "pooled_r3_minus_hybrid": true,
            "mean_paired_r3_minus_hybrid": false
          }
        },
        "fact_coverage": {
          "judges": {
            "original": {
              "pooled_r3_minus_hybrid": 0.042553191489361764,
              "mean_paired_r3_minus_hybrid": 0.04824561403508772,
              "n_pairs": 57
            },
            "second": {
              "pooled_r3_minus_hybrid": 0.04255319148936165,
              "mean_paired_r3_minus_hybrid": 0.042397660818713455,
              "n_pairs": 57
            }
          },
          "sign_flip": {
            "pooled_r3_minus_hybrid": false,
            "mean_paired_r3_minus_hybrid": false
          }
        }
      },
      "dev": {
        "claim_support": {
          "judges": {
            "original": {
              "pooled_r3_minus_hybrid": -0.002904989747095077,
              "mean_paired_r3_minus_hybrid": -0.04431818181818182,
              "n_pairs": 44
            },
            "second": {
              "pooled_r3_minus_hybrid": -0.014524948735475052,
              "mean_paired_r3_minus_hybrid": -0.0428030303030303,
              "n_pairs": 44
            }
          },
          "sign_flip": {
            "pooled_r3_minus_hybrid": false,
            "mean_paired_r3_minus_hybrid": false
          }
        },
        "fact_coverage": {
          "judges": {
            "original": {
              "pooled_r3_minus_hybrid": 0.06944444444444442,
              "mean_paired_r3_minus_hybrid": 0.07142857142857142,
              "n_pairs": 42
            },
            "second": {
              "pooled_r3_minus_hybrid": 0.06944444444444453,
              "mean_paired_r3_minus_hybrid": 0.0634920634920635,
              "n_pairs": 42
            }
          },
          "sign_flip": {
            "pooled_r3_minus_hybrid": false,
            "mean_paired_r3_minus_hybrid": false
          }
        }
      },
      "heldout": {
        "claim_support": {
          "judges": {
            "original": {
              "pooled_r3_minus_hybrid": 0.2727272727272727,
              "mean_paired_r3_minus_hybrid": 0.22222222222222224,
              "n_pairs": 6
            },
            "second": {
              "pooled_r3_minus_hybrid": 0.0,
              "mean_paired_r3_minus_hybrid": -0.027777777777777773,
              "n_pairs": 6
            }
          },
          "sign_flip": {
            "pooled_r3_minus_hybrid": false,
            "mean_paired_r3_minus_hybrid": true
          }
        },
        "fact_coverage": {
          "judges": {
            "original": {
              "pooled_r3_minus_hybrid": 0.0,
              "mean_paired_r3_minus_hybrid": 0.0,
              "n_pairs": 6
            },
            "second": {
              "pooled_r3_minus_hybrid": 0.0,
              "mean_paired_r3_minus_hybrid": 0.0,
              "n_pairs": 6
            }
          },
          "sign_flip": {
            "pooled_r3_minus_hybrid": false,
            "mean_paired_r3_minus_hybrid": false
          }
        }
      },
      "fresh": {
        "claim_support": {
          "judges": {
            "original": {
              "pooled_r3_minus_hybrid": 0.0,
              "mean_paired_r3_minus_hybrid": 0.0,
              "n_pairs": 9
            },
            "second": {
              "pooled_r3_minus_hybrid": 0.0,
              "mean_paired_r3_minus_hybrid": 0.0,
              "n_pairs": 9
            }
          },
          "sign_flip": {
            "pooled_r3_minus_hybrid": false,
            "mean_paired_r3_minus_hybrid": false
          }
        },
        "fact_coverage": {
          "judges": {
            "original": {
              "pooled_r3_minus_hybrid": -0.0714285714285714,
              "mean_paired_r3_minus_hybrid": -0.027777777777777776,
              "n_pairs": 9
            },
            "second": {
              "pooled_r3_minus_hybrid": -0.0714285714285714,
              "mean_paired_r3_minus_hybrid": -0.027777777777777776,
              "n_pairs": 9
            }
          },
          "sign_flip": {
            "pooled_r3_minus_hybrid": false,
            "mean_paired_r3_minus_hybrid": false
          }
        }
      }
    }
  },
  "denominators": {
    "gpt-5.6-luna/all": {
      "sampled_items": 120,
      "valid_items": 118,
      "judge_omitted_items": 2,
      "sampled_pairs": 60,
      "analysed_pairs": 58,
      "excluded_pairs": 2
    },
    "gpt-5.6-luna/dev": {
      "sampled_items": 88,
      "valid_items": 88,
      "judge_omitted_items": 0,
      "sampled_pairs": 44,
      "analysed_pairs": 44,
      "excluded_pairs": 0
    },
    "gpt-5.6-luna/heldout": {
      "sampled_items": 12,
      "valid_items": 11,
      "judge_omitted_items": 1,
      "sampled_pairs": 6,
      "analysed_pairs": 5,
      "excluded_pairs": 1
    },
    "gpt-5.6-luna/fresh": {
      "sampled_items": 20,
      "valid_items": 19,
      "judge_omitted_items": 1,
      "sampled_pairs": 10,
      "analysed_pairs": 9,
      "excluded_pairs": 1
    },
    "gpt-6-luna/all": {
      "sampled_items": 120,
      "valid_items": 119,
      "judge_omitted_items": 1,
      "sampled_pairs": 60,
      "analysed_pairs": 59,
      "excluded_pairs": 1
    },
    "gpt-6-luna/dev": {
      "sampled_items": 90,
      "valid_items": 89,
      "judge_omitted_items": 1,
      "sampled_pairs": 45,
      "analysed_pairs": 44,
      "excluded_pairs": 1
    },
    "gpt-6-luna/heldout": {
      "sampled_items": 12,
      "valid_items": 12,
      "judge_omitted_items": 0,
      "sampled_pairs": 6,
      "analysed_pairs": 6,
      "excluded_pairs": 0
    },
    "gpt-6-luna/fresh": {
      "sampled_items": 18,
      "valid_items": 18,
      "judge_omitted_items": 0,
      "sampled_pairs": 9,
      "analysed_pairs": 9,
      "excluded_pairs": 0
    }
  },
  "excluded_valid_partners": [
    {
      "model": "gpt-6-luna",
      "set": "dev",
      "case_id": "DEV-316",
      "arm": "r3",
      "family": "cross_source_synthesis"
    },
    {
      "model": "gpt-5.6-luna",
      "set": "fresh",
      "case_id": "HO-V2-044",
      "arm": "hybrid",
      "family": "cross_source_synthesis"
    },
    {
      "model": "gpt-5.6-luna",
      "set": "heldout",
      "case_id": "HO-003",
      "arm": "hybrid",
      "family": "factual_lookup"
    }
  ],
  "judge_omitted": {
    "count": 3,
    "by_family": {
      "cross_source_synthesis": 2,
      "factual_lookup": 1
    },
    "by_arm": {
      "gpt-6-luna/hybrid": 1,
      "gpt-5.6-luna/r3": 2
    },
    "items": [
      {
        "case_id": "DEV-316",
        "family": "cross_source_synthesis",
        "model": "gpt-6-luna",
        "set": "dev",
        "arm": "hybrid",
        "status": "judge_omitted",
        "reason": "incomplete_or_duplicate_or_extra_indices",
        "original": {
          "claims": [
            "supported",
            "supported",
            "supported"
          ],
          "facts": [
            "covered",
            "covered"
          ]
        },
        "second": null,
        "attempts": [
          {
            "attempt": 0,
            "cached": true,
            "usage": {
              "input_tokens": 1951,
              "output_tokens": 211
            },
            "list_price_usd": 0.006012,
            "status": "invalid_indices",
            "diagnostics": {
              "claims": {
                "expected": 3,
                "returned": 4,
                "indices": [
                  0,
                  1,
                  2,
                  2
                ]
              },
              "facts": {
                "expected": 2,
                "returned": 2,
                "indices": [
                  0,
                  1
                ]
              }
            }
          },
          {
            "attempt": 1,
            "cached": false,
            "usage": {
              "input_tokens": 1951,
              "output_tokens": 230
            },
            "list_price_usd": 0.006202,
            "status": "invalid_indices",
            "diagnostics": {
              "claims": {
                "expected": 3,
                "returned": 4,
                "indices": [
                  0,
                  1,
                  2,
                  2
                ]
              },
              "facts": {
                "expected": 2,
                "returned": 2,
                "indices": [
                  0,
                  1
                ]
              }
            }
          }
        ]
      },
      {
        "case_id": "HO-V2-044",
        "family": "cross_source_synthesis",
        "model": "gpt-5.6-luna",
        "set": "fresh",
        "arm": "r3",
        "status": "judge_omitted",
        "reason": "incomplete_or_duplicate_or_extra_indices",
        "original": {
          "claims": [
            "supported",
            "supported",
            "supported",
            "supported"
          ],
          "facts": [
            "covered"
          ]
        },
        "second": null,
        "attempts": [
          {
            "attempt": 0,
            "cached": false,
            "usage": {
              "input_tokens": 2488,
              "output_tokens": 200
            },
            "list_price_usd": 0.006976,
            "status": "invalid_indices",
            "diagnostics": {
              "claims": {
                "expected": 4,
                "returned": 5,
                "indices": [
                  0,
                  1,
                  2,
                  3,
                  4
                ]
              },
              "facts": {
                "expected": 1,
                "returned": 1,
                "indices": [
                  0
                ]
              }
            }
          },
          {
            "attempt": 1,
            "cached": false,
            "usage": {
              "input_tokens": 2488,
              "output_tokens": 213
            },
            "list_price_usd": 0.007106,
            "status": "invalid_indices",
            "diagnostics": {
              "claims": {
                "expected": 4,
                "returned": 5,
                "indices": [
                  0,
                  1,
                  2,
                  3,
                  4
                ]
              },
              "facts": {
                "expected": 1,
                "returned": 1,
                "indices": [
                  0
                ]
              }
            }
          }
        ]
      },
      {
        "case_id": "HO-003",
        "family": "factual_lookup",
        "model": "gpt-5.6-luna",
        "set": "heldout",
        "arm": "r3",
        "status": "judge_omitted",
        "reason": "incomplete_or_duplicate_or_extra_indices",
        "original": {
          "claims": [
            "supported"
          ],
          "facts": [
            "missing"
          ]
        },
        "second": null,
        "attempts": [
          {
            "attempt": 0,
            "cached": false,
            "usage": {
              "input_tokens": 1298,
              "output_tokens": 180
            },
            "list_price_usd": 0.004396,
            "status": "invalid_indices",
            "diagnostics": {
              "claims": {
                "expected": 1,
                "returned": 2,
                "indices": [
                  0,
                  0
                ]
              },
              "facts": {
                "expected": 1,
                "returned": 1,
                "indices": [
                  0
                ]
              }
            }
          },
          {
            "attempt": 1,
            "cached": false,
            "usage": {
              "input_tokens": 1298,
              "output_tokens": 200
            },
            "list_price_usd": 0.004596,
            "status": "invalid_indices",
            "diagnostics": {
              "claims": {
                "expected": 1,
                "returned": 2,
                "indices": [
                  0,
                  1
                ]
              },
              "facts": {
                "expected": 1,
                "returned": 1,
                "indices": [
                  0
                ]
              }
            }
          }
        ]
      }
    ]
  },
  "omission_problem": true,
  "incompleteness_warning": "Rates and agreement are conditional on valid pairs; omitted items are not imputed.",
  "low_kappa_problem": true,
  "sign_flip_problem": true
}
```

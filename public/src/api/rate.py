rate = {
  'CA': {
    'per_job': 570.89,
    'annual': 137013.26
  },
  'FL': {
    'per_job': 364.47,
    'annual': 87472.83
  },
  'TX': {
    'per_job': 395.24,
    'annual': 94857.74
  },
  'WA': {
    'per_job': 595.25,
    'annual': 142859.65
  },
  'NY': {
    'per_job': 615.76,
    'annual': 147782.92
  },
  'NJ ': {
    'per_job': 602.14,
    'annual': 144513.56
  },
  'AZ': {
    'per_job': 381.46,
    'annual': 91549.92
  },
  'IL': {
    'per_job': 626.82,
    'annual': 150436.87
  },
  'CO': {
    'per_job': 436.59,
    'annual': 104781.21
  },
  'GA': {
    'per_job': 408.38,
    'annual': 98011.71
  },
  'OR': {
    'per_job': 611.92,
    'annual': 146859.81
  },
  'MA': {
    'per_job': 570.73,
    'annual': 136974.80
  },
  'VA': {
    'per_job': 437.39,
    'annual': 104973.53
  },
  'MD': {
    'per_job': 468.80,
    'annual': 112512.29
  },
  'PA': {
    'per_job': 515.28,
    'annual': 123666.58
  },
  'NC': {
    'per_job': 354.37,
    'annual': 85049.66
  },
  'OH': {
    'per_job': 434.02,
    'annual': 104165.80
  },
  'UT': {
    'per_job': 426.97,
    'annual': 102473.43
  },
  'NV': {
    'per_job': 500.37,
    'annual': 120089.51
  },
  'HI': {
    'per_job': 597.17,
    'annual': 143321.20
  },
  'MI': {
    'per_job': 470.24,
    'annual': 112858.46
  },
  'MN': {
    'per_job': 517.68,
    'annual': 124243.52
  },
  'CT': {
    'per_job': 510.79,
    'annual': 122589.61
  },
  'TN': {
    'per_job': 388.51,
    'annual': 93242.29
  },
  'IN': {
    'per_job': 475.05,
    'annual': 114012.35
  },
  'MO': {
    'per_job': 460.95,
    'annual': 110627.60
  },
  'WI': {
    'per_job': 485.63,
    'annual': 116550.91
  },
  'SI': {
    'per_job': 363.99,
    'annual': 87357.44
  },
  'OK': {
    'per_job': 417.68,
    'annual': 100242.57
  },
  'KS': {
    'per_job': 423.93,
    'annual': 101742.63
  },
  'AL': {
    'per_job': 359.02,
    'annual': 86165.09
  },
  'NH': {
    'per_job': 439.95,
    'annual': 105588.94
  },
  'KY': {
    'per_job': 397.48,
    'annual': 95396.23
  },
  'NM': {
    'per_job': 407.42,
    'annual': 97780.94
  },
  'DC': {
    'per_job': 589.00,
    'annual': 141359.59
  },
  'ID': {
    'per_job': 388.35,
    'annual': 93203.83
  },
  'IA': {
    'per_job': 423.45,
    'annual': 101627.24
  },
  'VT': {
    'per_job': 388.51,
    'annual': 93242.29
  },
  'DE': {
    'per_job': 413.03,
    'annual': 99127.14
  },
  'LA': {
    'per_job': 412.87,
    'annual': 99088.68
  },
  'ME': {
    'per_job': 434.02,
    'annual': 104165.80
  },
  'NE': {
    'per_job': 387.87,
    'annual': 93088.44
  },
  'RI': {
    'per_job': 448.13,
    'annual': 107550.55
  },
  'AR': {
    'per_job': 330.98,
    'annual': 79434.05
  },
  'AK': {
    'per_job': 602.46,
    'annual': 144590.49
  },
  'MT': {
    'per_job': 457.10,
    'annual': 109704.49
  },
  'MS': {
    'per_job': 404.22,
    'annual': 97011.67
  },
  'WV': {
    'per_job': 445.40,
    'annual': 106896.68
  },
  'SD': {
    'per_job': 385.14,
    'annual': 92434.57
  },
  'WY': {
    'per_job': 472.65,
    'annual': 113435.40
  },
  'ND': {
    'per_job': 508.23,
    'annual': 121974.20
  },
}


def get_rate(state: str):
    """
    Returns an object with the per job and annual potential earnings for an installer
    per state, or an object with the values 0
    """
    return rate.get(state, {
        'per_job': 0,
        'annual': 0
    })

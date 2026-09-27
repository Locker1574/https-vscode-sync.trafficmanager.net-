export type Mode = "surete" | "equilibre" | "rendement";
export type Status = "V" | "P" | "R" | null;

export interface Market {
  matchId: string;
  key: string;
  group: string;
  label: string;
  p: number;
  confidence: number;
  fairOdds: number;
  odds: number | null;
  value: number | null;
  status?: Status;
}

export interface MatchInfo {
  id: string;
  league: string;
  date: string;
  time: string | null;
  home: string;
  away: string;
}

export interface Selection extends Market {
  match: string;
  date: string;
  time: string | null;
  locked?: boolean;
  isNew?: boolean;
}

export interface CouponResult {
  selections: Selection[];
  combinedProbability: number;
  totalOdds: number;
  size: number;
}

export interface RegenerateResult extends CouponResult {
  replaced: number;
  message: string;
  alternative: CouponResult;
}

export interface Transaction {
    Date: string;
    Description: string;
    Amount: number;
    Type: string;
    Balance: number | null;
    Category: string;
    Merchant: string | null;
    SourceFile: string | null;
    ImportedAt: string | null;
}

export interface MonthlyTrendItem {
    Month: string;
    Income: number;
    Expense: number;
}

export interface StatsData {
    total_income: number;
    total_spend: number;
    savings_rate: number;
    monthly_trend: MonthlyTrendItem[];
}

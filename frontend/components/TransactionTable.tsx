"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { motion } from "framer-motion"
import { Search } from "lucide-react"
import { useState } from "react"
import { cn } from "@/lib/utils"

import { Transaction } from "@/types"

export function TransactionTable({ initialData }: { initialData: Transaction[] }) {
    const [filter, setFilter] = useState("")

    const filtered = initialData.filter(t =>
        t.Description.toLowerCase().includes(filter.toLowerCase()) ||
        (t.Category || "").toLowerCase().includes(filter.toLowerCase()) ||
        (t.Merchant || "").toLowerCase().includes(filter.toLowerCase())
    ).slice(0, 50) // Limit for performance

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="p-4"
        >
            <Card className="glass-panel border-white/5">
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>Recent Transactions</CardTitle>
                    <div className="relative">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <input
                            type="text"
                            placeholder="Search..."
                            className="h-9 w-[250px] rounded-md bg-secondary/50 pl-8 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-1 focus-visible:ring-ring"
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                        />
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="relative w-full overflow-auto">
                        <table className="w-full caption-bottom text-sm text-left">
                            <thead className="[&_tr]:border-b [&_tr]:border-white/10">
                                <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                                    <th className="h-12 px-4 align-middle font-medium text-muted-foreground">Date</th>
                                    <th className="h-12 px-4 align-middle font-medium text-muted-foreground">Merchant</th>
                                    <th className="h-12 px-4 align-middle font-medium text-muted-foreground">Category</th>
                                    <th className="h-12 px-4 align-middle font-medium text-muted-foreground text-right">Amount</th>
                                </tr>
                            </thead>
                            <tbody className="[&_tr:last-child]:border-0">
                                {filtered.map((t, i) => (
                                    <tr key={i} className="border-b border-white/5 transition-colors hover:bg-white/5">
                                        <td className="p-4 align-middle">{t.Date}</td>
                                        <td className="p-4 align-middle font-medium">{t.Merchant || t.Description}</td>
                                        <td className="p-4 align-middle">
                                            <span className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
                                                {t.Category}
                                            </span>
                                        </td>
                                        <td className={cn("p-4 align-middle text-right font-medium", t.Amount > 0 ? "text-emerald-400" : "text-white")}>
                                            {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Math.abs(t.Amount))}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {filtered.length === 0 && (
                            <div className="text-center py-10 text-muted-foreground">
                                No transactions found.
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    )
}

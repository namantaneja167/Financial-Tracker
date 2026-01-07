"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { ArrowLeft, CreditCard, Calendar, Zap, AlertTriangle } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import Link from "next/link"

interface SubscriptionItem {
    merchant: string
    amount: number
    frequency: string
    yearly_cost: number
    last_paid: string
}

interface SubscriptionResponse {
    total_monthly: number
    items: SubscriptionItem[]
}

export default function SubscriptionsPage() {
    const [data, setData] = useState<SubscriptionResponse | null>(null)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        fetch("http://127.0.0.1:8000/api/subscriptions")
            .then(res => res.json())
            .then(setData)
            .catch(console.error)
            .finally(() => setIsLoading(false))
    }, [])

    const formatCurrency = (val: number) =>
        new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val)

    return (
        <div className="min-h-screen bg-background text-foreground p-6 md:p-12 relative">
            {/* Background Ambience */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
                <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-500/10 rounded-full blur-[100px]" />
            </div>

            {/* Header */}
            <div className="max-w-6xl mx-auto mb-12">
                <Link href="/" className="inline-flex items-center text-muted-foreground hover:text-foreground mb-6 transition-colors">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Dashboard
                </Link>
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                    <div>
                        <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                            Recurring Expenses
                        </h1>
                        <p className="text-muted-foreground mt-2">
                            Auto-detected subscriptions and fixed costs.
                        </p>
                    </div>
                    {data && (
                        <div className="text-right">
                            <p className="text-sm text-muted-foreground">Est. Monthly Cost</p>
                            <div className="text-3xl font-bold text-white">
                                {formatCurrency(data.total_monthly)}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="max-w-6xl mx-auto">
                {isLoading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-48 rounded-xl bg-white/5 animate-pulse" />
                        ))}
                    </div>
                ) : data?.items.length === 0 ? (
                    <div className="text-center py-20 bg-white/5 rounded-2xl border border-white/10">
                        <Zap className="h-12 w-12 text-yellow-400 mx-auto mb-4" />
                        <h3 className="text-xl font-medium text-white">No Subscriptions Detected</h3>
                        <p className="text-muted-foreground mt-2 max-w-md mx-auto">
                            We couldn't find regular recurring payments clearly in your transaction history.
                            Try uploading more months of data!
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {data?.items.map((sub, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.1 }}
                            >
                                <Card className="glass-panel border-white/10 hover:border-purple-500/30 transition-colors group">
                                    <CardHeader className="flex flex-row items-start justify-between pb-2">
                                        <div className="h-10 w-10 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-400 group-hover:bg-purple-500/20 transition-colors">
                                            <CreditCard className="h-5 w-5" />
                                        </div>
                                        <div className="bg-white/5 px-2 py-1 rounded text-xs font-mono text-zinc-400 border border-white/5">
                                            {sub.frequency}
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        <h3 className="font-semibold text-lg text-white mb-1 truncate">{sub.merchant}</h3>
                                        <div className="text-2xl font-bold text-purple-200 mb-4">
                                            {formatCurrency(sub.amount)}
                                            <span className="text-sm font-normal text-muted-foreground ml-1">/mo</span>
                                        </div>

                                        <div className="space-y-2 pt-4 border-t border-white/5 text-sm">
                                            <div className="flex justify-between text-muted-foreground">
                                                <span className="flex items-center"><Calendar className="h-3 w-3 mr-1" /> Last Paid</span>
                                                <span className="text-zinc-300">{sub.last_paid}</span>
                                            </div>
                                            <div className="flex justify-between text-muted-foreground">
                                                <span className="flex items-center"><AlertTriangle className="h-3 w-3 mr-1" /> Yearly Impact</span>
                                                <span className="text-zinc-300">{formatCurrency(sub.yearly_cost)}</span>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}

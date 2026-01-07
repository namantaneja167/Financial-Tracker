"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { motion } from "framer-motion"
import { ArrowUpRight, ArrowDownRight, DollarSign, Wallet, PiggyBank, TrendingUp } from "lucide-react"
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis } from "recharts"

import { StatsData } from "@/types"

export function BentoGrid({ data }: { data: StatsData }) {
    const formatCurrency = (val: number) =>
        new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val)

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4">
            {/* Total Income */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="col-span-1"
            >
                <Card className="h-full bg-blue-500/10 border-blue-500/20">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-blue-400">Total Income</CardTitle>
                        <Wallet className="h-4 w-4 text-blue-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-blue-100">{formatCurrency(data.total_income)}</div>
                        <p className="text-xs text-blue-400/80 flex items-center mt-1">
                            <ArrowUpRight className="h-3 w-3 mr-1" />
                            +12.5% from last month
                        </p>
                    </CardContent>
                </Card>
            </motion.div>

            {/* Total Spend */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.1 }}
                className="col-span-1"
            >
                <Card className="h-full bg-purple-500/10 border-purple-500/20">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-purple-400">Total Spend</CardTitle>
                        <DollarSign className="h-4 w-4 text-purple-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-purple-100">{formatCurrency(data.total_spend)}</div>
                        <p className="text-xs text-purple-400/80 flex items-center mt-1">
                            <ArrowDownRight className="h-3 w-3 mr-1" />
                            -2.1% from last month
                        </p>
                    </CardContent>
                </Card>
            </motion.div>

            {/* Savings Rate */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.2 }}
                className="col-span-1"
            >
                <Card className="h-full bg-emerald-500/10 border-emerald-500/20">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-emerald-400">Savings Rate</CardTitle>
                        <PiggyBank className="h-4 w-4 text-emerald-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-emerald-100">{data.savings_rate.toFixed(1)}%</div>
                        <p className="text-xs text-emerald-400/80 mt-1">
                            Target: 20%
                        </p>
                    </CardContent>
                </Card>
            </motion.div>

            {/* Net Worth (Placeholder/Calculated) */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.3 }}
                className="col-span-1"
            >
                <Card className="h-full bg-amber-500/10 border-amber-500/20">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-amber-400">Net Worth</CardTitle>
                        <TrendingUp className="h-4 w-4 text-amber-400" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-amber-100">{formatCurrency(data.total_income - data.total_spend)}</div>
                        <p className="text-xs text-amber-400/80 mt-1">
                            Based on cash flow
                        </p>
                    </CardContent>
                </Card>
            </motion.div>

            {/* Large Chart Area */}
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4, delay: 0.4 }}
                className="col-span-1 md:col-span-2 lg:col-span-4 min-h-[300px]"
            >
                <Card className="h-full glass-panel border-white/5">
                    <CardHeader>
                        <CardTitle className="text-lg">Monthly Trends</CardTitle>
                    </CardHeader>
                    <CardContent className="min-w-0 p-0">
                        <div className="h-[250px] w-full relative">
                            <div className="absolute inset-0">
                                <ResponsiveContainer width="100%" height="100%" minWidth={0} debounce={1}>
                                    <LineChart data={data.monthly_trend}>
                                        <XAxis
                                            dataKey="Month"
                                            stroke="#525252"
                                            fontSize={12}
                                            tickLine={false}
                                            axisLine={false}
                                        />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a' }}
                                            itemStyle={{ color: '#fafafa' }}
                                        />
                                        <Line
                                            type="monotone"
                                            dataKey="Income"
                                            stroke="#3b82f6"
                                            strokeWidth={2}
                                            dot={false}
                                        />
                                        <Line
                                            type="monotone"
                                            dataKey="Expense"
                                            stroke="#a855f7"
                                            strokeWidth={2}
                                            dot={false}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>
        </div>
    )
}

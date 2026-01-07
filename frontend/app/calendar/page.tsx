"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { motion, AnimatePresence } from "framer-motion"
import { ArrowLeft, ChevronLeft, ChevronRight, X, Calendar as CalendarIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
    format,
    startOfMonth,
    endOfMonth,
    eachDayOfInterval,
    isSameMonth,
    isSameDay,
    addMonths,
    subMonths,
    getDay,
    parseISO
} from "date-fns"
import { Transaction } from "@/types"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogClose } from "@/components/ui/dialog"

// Helper to format currency
const formatMoney = (amount: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)

export default function CalendarPage() {
    const [transactions, setTransactions] = useState<Transaction[]>([])
    const [currentDate, setCurrentDate] = useState(new Date())
    const [selectedDate, setSelectedDate] = useState<Date | null>(null)
    const [isDialogOpen, setIsDialogOpen] = useState(false)

    // Fetch transactions on mount
    useEffect(() => {
        fetch("http://127.0.0.1:8000/api/transactions")
            .then(res => res.json())
            .then(data => setTransactions(data))
            .catch(console.error)
    }, [])

    // Navigation handlers
    const prevMonth = () => setCurrentDate(subMonths(currentDate, 1))
    const nextMonth = () => setCurrentDate(addMonths(currentDate, 1))

    // Grid Generation
    const monthStart = startOfMonth(currentDate)
    const monthEnd = endOfMonth(currentDate)
    const daysInMonth = eachDayOfInterval({ start: monthStart, end: monthEnd })

    // Padding days for grid alignment (0 = Sunday)
    const startDay = getDay(monthStart)
    const prefixDays = Array.from({ length: startDay })

    // Data Aggregation per Day
    const getDayData = (day: Date) => {
        const dayTxns = transactions.filter(t => {
            // Robust date comparison: try to parse t.Date correctly
            // Assuming t.Date is 'YYYY-MM-DD' string
            if (!t.Date) return false
            // Simple string comparison usually works for YYYY-MM-DD
            return t.Date === format(day, 'yyyy-MM-dd')
        })

        const income = dayTxns
            .filter(t => t.Amount > 0)
            .reduce((sum, t) => sum + t.Amount, 0)

        const expense = dayTxns
            .filter(t => t.Amount < 0)
            .reduce((sum, t) => sum + Math.abs(t.Amount), 0)

        return { income, expense, txns: dayTxns }
    }

    const handleDayClick = (day: Date) => {
        setSelectedDate(day)
        setIsDialogOpen(true)
    }

    const selectedDayData = selectedDate ? getDayData(selectedDate) : null

    return (
        <div className="min-h-screen bg-background text-foreground p-6 md:p-12 relative overflow-y-auto">
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
                <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-500/10 rounded-full blur-[100px]" />
                <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-500/10 rounded-full blur-[100px]" />
            </div>

            <div className="max-w-6xl mx-auto mb-8">
                <Link href="/" className="inline-flex items-center text-muted-foreground hover:text-foreground mb-6 transition-colors">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Dashboard
                </Link>

                <div className="flex flex-col md:flex-row items-center justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                            Fiscal Calendar
                        </h1>
                        <p className="text-zinc-400 mt-1">Daily view of your income and expenses.</p>
                    </div>

                    <div className="flex items-center gap-4 bg-white/5 p-2 rounded-full border border-white/10">
                        <Button variant="ghost" size="icon" onClick={prevMonth} className="hover:bg-white/10 rounded-full text-white">
                            <ChevronLeft className="h-4 w-4" />
                        </Button>
                        <span className="text-xl font-medium min-w-[140px] text-center text-white">
                            {format(currentDate, 'MMMM yyyy')}
                        </span>
                        <Button variant="ghost" size="icon" onClick={nextMonth} className="hover:bg-white/10 rounded-full text-white">
                            <ChevronRight className="h-4 w-4" />
                        </Button>
                    </div>
                </div>

                {/* Days Header */}
                <div className="grid grid-cols-7 gap-1 mb-2 text-center">
                    {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                        <div key={day} className="text-zinc-500 text-sm font-medium py-2 uppercase tracking-wider">
                            {day}
                        </div>
                    ))}
                </div>

                {/* Calendar Grid */}
                <div className="grid grid-cols-7 gap-1 auto-rows-fr">
                    {prefixDays.map((_, i) => (
                        <div key={`prefix-${i}`} className="p-4 bg-transparent border border-transparent" />
                    ))}

                    {daysInMonth.map((day) => {
                        const { income, expense, txns } = getDayData(day)
                        const hasActivity = txns.length > 0
                        const isNetPositive = income > expense

                        return (
                            <motion.div
                                key={day.toISOString()}
                                whileHover={{ scale: 1.02, backgroundColor: "rgba(255,255,255,0.08)" }}
                                onClick={() => handleDayClick(day)}
                                className={`
                            min-h-[120px] p-3 rounded-xl border border-white/5 cursor-pointer transition-colors relative group
                            ${hasActivity ? 'bg-white/5' : 'bg-transparent'}
                        `}
                            >
                                <span className={`text-sm font-medium ${isSameDay(day, new Date()) ? 'bg-blue-500 text-white w-6 h-6 rounded-full flex items-center justify-center' : 'text-zinc-400'}`}>
                                    {format(day, 'd')}
                                </span>

                                {hasActivity && (
                                    <div className="mt-2 space-y-1">
                                        {income > 0 && (
                                            <div className="text-xs font-medium text-emerald-400 flex justify-between">
                                                <span>In</span>
                                                <span>+{Math.round(income)}</span>
                                            </div>
                                        )}
                                        {expense > 0 && (
                                            <div className="text-xs font-medium text-rose-400 flex justify-between">
                                                <span>Out</span>
                                                <span>-{Math.round(expense)}</span>
                                            </div>
                                        )}

                                        <div className={`text-[10px] sm:text-xs mt-2 pt-2 border-t border-white/10 font-bold text-center ${isNetPositive ? 'text-emerald-500' : 'text-rose-500'}`}>
                                            {isNetPositive ? '+' : ''}{Math.round(income - expense)}
                                        </div>
                                    </div>
                                )}

                                {!hasActivity && (
                                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-20 pointer-events-none">
                                        <span className="text-xs text-zinc-500">No Data</span>
                                    </div>
                                )}
                            </motion.div>
                        )
                    })}
                </div>
            </div>

            {/* Details Dialog */}
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogContent className="bg-[#18181b] border-white/10 text-white max-w-md">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2 text-xl">
                            <CalendarIcon className="h-5 w-5 text-blue-400" />
                            {selectedDate && format(selectedDate, 'MMMM do, yyyy')}
                        </DialogTitle>
                    </DialogHeader>

                    <div className="mt-4 max-h-[60vh] overflow-y-auto pr-2 custom-scrollbar">
                        {selectedDayData?.txns.length === 0 ? (
                            <div className="text-center py-8 text-zinc-500">
                                No transactions on this day.
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {selectedDayData?.txns.map((t, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-black/20 border border-white/5 hover:bg-black/40 transition-colors">
                                        <div className="flex-1 min-w-0 mr-4">
                                            <p className="font-medium text-sm truncate text-white">{t.Description}</p>
                                            <p className="text-xs text-zinc-400">{t.Category} • {t.Merchant}</p>
                                        </div>
                                        <p className={`font-mono font-bold whitespace-nowrap ${t.Amount > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                            {t.Amount > 0 ? '+' : ''}{formatMoney(t.Amount)}
                                        </p>
                                    </div>
                                ))}

                                <div className="mt-6 pt-4 border-t border-white/10 flex justify-between items-center px-2">
                                    <div className="text-right flex-1">
                                        <p className="text-xs text-zinc-400">Net Daily Total</p>
                                        <p className={`text-lg font-bold ${selectedDayData && (selectedDayData.income - selectedDayData.expense) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                            {selectedDayData && formatMoney(selectedDayData.income - selectedDayData.expense)}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    )
}

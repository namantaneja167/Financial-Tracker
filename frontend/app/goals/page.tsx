"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { ArrowLeft, Target, Plus, PiggyBank, Trash2, CheckCircle, TrendingUp } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { PieChart, Pie, Cell } from "recharts"

interface GoalItem {
    id: number
    name: string
    target_amount: number
    current_amount: number
    target_date: string | null
    icon: string | null
    is_completed: boolean
}

export default function GoalsPage() {
    const [goals, setGoals] = useState<GoalItem[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [newGoal, setNewGoal] = useState({ name: "", target_amount: "", target_date: "" })
    const [contribution, setContribution] = useState({ id: 0, amount: "" })
    const [isOpen, setIsOpen] = useState(false)

    useEffect(() => {
        fetchGoals()
    }, [])

    const fetchGoals = () => {
        fetch("http://127.0.0.1:8000/api/goals")
            .then(res => res.json())
            .then(setGoals)
            .catch(console.error)
            .finally(() => setIsLoading(false))
    }

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault()
        await fetch("http://127.0.0.1:8000/api/goals", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: newGoal.name,
                target_amount: parseFloat(newGoal.target_amount),
                target_date: newGoal.target_date || null
            })
        })
        setNewGoal({ name: "", target_amount: "", target_date: "" })
        setIsOpen(false)
        fetchGoals()
    }

    const handleContribute = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!contribution.amount) return
        await fetch(`http://127.0.0.1:8000/api/goals/${contribution.id}/contribute`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ amount: parseFloat(contribution.amount) })
        })
        setContribution({ id: 0, amount: "" })
        fetchGoals()
    }

    const handleDelete = async (id: number) => {
        await fetch(`http://127.0.0.1:8000/api/goals/${id}`, { method: "DELETE" })
        fetchGoals()
    }

    const formatCurrency = (val: number) =>
        new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val)

    return (
        <div className="min-h-screen bg-background text-foreground p-6 md:p-12 relative overflow-y-auto">
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
                <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-500/10 rounded-full blur-[100px]" />
            </div>

            <div className="max-w-6xl mx-auto mb-12">
                <Link href="/" className="inline-flex items-center text-muted-foreground hover:text-foreground mb-6 transition-colors">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Dashboard
                </Link>
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div>
                        <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
                            Financial Goals
                        </h1>
                        <p className="text-muted-foreground mt-2">
                            Track your savings targets.
                        </p>
                    </div>

                    <Dialog open={isOpen} onOpenChange={setIsOpen}>
                        <DialogTrigger asChild>
                            <Button className="bg-emerald-500 hover:bg-emerald-600 text-white rounded-full">
                                <Plus className="h-4 w-4 mr-2" /> New Goal
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="bg-[#18181b] border-white/10 text-white">
                            <DialogHeader>
                                <DialogTitle>Create New Goal</DialogTitle>
                            </DialogHeader>
                            <form onSubmit={handleCreate} className="space-y-4 mt-4">
                                <div>
                                    <label className="block text-sm text-zinc-400 mb-1">Goal Name</label>
                                    <input
                                        type="text"
                                        required
                                        value={newGoal.name}
                                        onChange={e => setNewGoal({ ...newGoal, name: e.target.value })}
                                        className="w-full bg-black/50 border border-white/10 rounded-md p-2 text-white"
                                        placeholder="e.g. New Car"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-zinc-400 mb-1">Target Amount ($)</label>
                                    <input
                                        type="number"
                                        required
                                        value={newGoal.target_amount}
                                        onChange={e => setNewGoal({ ...newGoal, target_amount: e.target.value })}
                                        className="w-full bg-black/50 border border-white/10 rounded-md p-2 text-white"
                                        placeholder="5000"
                                    />
                                </div>
                                <Button type="submit" className="w-full bg-emerald-500 hover:bg-emerald-600">
                                    Create Goal
                                </Button>
                            </form>
                        </DialogContent>
                    </Dialog>
                </div>
            </div>

            <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {goals.map((goal) => {
                    const percent = Math.min(100, (goal.current_amount / goal.target_amount) * 100)
                    const data = [{ value: percent }, { value: 100 - percent }]

                    return (
                        <motion.div
                            key={goal.id}
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                        >
                            <Card className="glass-panel border-white/10 relative overflow-hidden group">
                                <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <Button variant="ghost" size="icon" className="h-8 w-8 text-red-400 hover:text-red-300 hover:bg-red-500/10" onClick={() => handleDelete(goal.id)}>
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>

                                <CardContent className="pt-6 flex flex-col items-center text-center">
                                    <div className="relative w-32 h-32 mb-4">
                                        <PieChart width={128} height={128}>
                                            <Pie
                                                data={data}
                                                cx={60}
                                                cy={60}
                                                innerRadius={45}
                                                outerRadius={58}
                                                startAngle={90}
                                                endAngle={-270}
                                                dataKey="value"
                                                stroke="none"
                                            >
                                                <Cell fill="#10b981" />
                                                <Cell fill="#27272a" />
                                            </Pie>
                                        </PieChart>
                                        <div className="absolute inset-0 flex items-center justify-center flex-col">
                                            <span className="text-xl font-bold text-white">{percent.toFixed(0)}%</span>
                                        </div>
                                    </div>

                                    <h3 className="text-lg font-semibold text-white mb-1">{goal.name}</h3>
                                    <p className="text-sm text-zinc-400 mb-6">
                                        {formatCurrency(goal.current_amount)} / {formatCurrency(goal.target_amount)}
                                    </p>

                                    {goal.is_completed ? (
                                        <div className="w-full py-2 bg-emerald-500/20 text-emerald-400 rounded-lg flex items-center justify-center font-medium">
                                            <CheckCircle className="h-4 w-4 mr-2" /> Completed
                                        </div>
                                    ) : (
                                        <form onSubmit={(e) => { e.preventDefault(); handleContribute(e); }} className="w-full flex gap-2">
                                            <input
                                                type="number"
                                                placeholder="Add $"
                                                className="flex-1 bg-black/50 border border-white/10 rounded-md px-3 py-1 text-sm text-white focus:outline-none focus:border-emerald-500/50"
                                                value={contribution.id === goal.id ? contribution.amount : ""}
                                                onChange={e => setContribution({ id: goal.id, amount: e.target.value })}
                                            />
                                            <Button type="submit" size="sm" className="bg-white/10 hover:bg-white/20 text-white" disabled={contribution.id !== goal.id || !contribution.amount}>
                                                <Plus className="h-4 w-4" />
                                            </Button>
                                        </form>
                                    )}
                                </CardContent>
                            </Card>
                        </motion.div>
                    )
                })}
            </div>
        </div>
    )
}

"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowLeft, TrendingUp, Plus, Trash2, DollarSign, Wallet, Building, Bitcoin } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts"

interface AssetItem {
    id: number
    name: string
    type: string
    quantity: number
    value: number
    last_updated: string | null
}

interface PortfolioResponse {
    net_worth: number
    total_assets: number
    total_liabilities: number
    assets: AssetItem[]
}

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899', '#6366f1'];

export default function PortfolioPage() {
    const [data, setData] = useState<PortfolioResponse | null>(null)
    const [loading, setLoading] = useState(true)
    const [isDialogOpen, setIsDialogOpen] = useState(false)
    const [newAsset, setNewAsset] = useState({ name: "", type: "Stock", value: "", quantity: "1" })

    useEffect(() => {
        fetchPortfolio()
    }, [])

    const fetchPortfolio = () => {
        fetch("http://127.0.0.1:8000/api/portfolio")
            .then(res => res.json())
            .then(setData)
            .catch(console.error)
            .finally(() => setLoading(false))
    }

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault()
        await fetch("http://127.0.0.1:8000/api/portfolio", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: newAsset.name,
                type: newAsset.type,
                value: parseFloat(newAsset.value),
                quantity: parseFloat(newAsset.quantity)
            })
        })
        setNewAsset({ name: "", type: "Stock", value: "", quantity: "1" })
        setIsDialogOpen(false)
        fetchPortfolio()
    }

    const handleDelete = async (id: number) => {
        await fetch(`http://127.0.0.1:8000/api/portfolio/${id}`, { method: "DELETE" })
        fetchPortfolio()
    }

    const formatMoney = (val: number) =>
        new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val)

    if (loading) return <div className="p-12 text-center text-zinc-500">Loading portfolio...</div>

    const assetDistribution = data?.assets
        .filter(a => a.type !== 'Liability')
        .map(a => ({ name: a.name, value: a.value })) || []

    return (
        <div className="min-h-screen bg-background text-foreground p-6 md:p-12 relative overflow-y-auto">
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
                <div className="absolute top-[-10%] left-[20%] w-[50%] h-[50%] bg-emerald-500/10 rounded-full blur-[120px]" />
            </div>

            <div className="max-w-6xl mx-auto">
                <Link href="/" className="inline-flex items-center text-muted-foreground hover:text-foreground mb-6 transition-colors">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Dashboard
                </Link>

                <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-8">
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                        Net Worth
                    </h1>
                    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                        <DialogTrigger asChild>
                            <Button className="bg-emerald-500 hover:bg-emerald-600 text-white rounded-full">
                                <Plus className="h-4 w-4 mr-2" /> Add Asset
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="bg-[#18181b] border-white/10 text-white">
                            <DialogHeader>
                                <DialogTitle>Add Asset or Liability</DialogTitle>
                            </DialogHeader>
                            <form onSubmit={handleCreate} className="space-y-4 mt-4">
                                <div>
                                    <label className="block text-sm text-zinc-400 mb-1">Name</label>
                                    <input
                                        type="text"
                                        required
                                        value={newAsset.name}
                                        onChange={e => setNewAsset({ ...newAsset, name: e.target.value })}
                                        className="w-full bg-black/50 border border-white/10 rounded-md p-2 text-white"
                                        placeholder="e.g. AAPL Stock"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-zinc-400 mb-1">Type</label>
                                    <select
                                        value={newAsset.type}
                                        onChange={e => setNewAsset({ ...newAsset, type: e.target.value })}
                                        className="w-full bg-black/50 border border-white/10 rounded-md p-2 text-white"
                                    >
                                        <option value="Stock">Stock/ETF</option>
                                        <option value="Crypto">Crypto</option>
                                        <option value="Real Estate">Real Estate</option>
                                        <option value="Cash">Cash</option>
                                        <option value="Liability">Liability (Loan/Debt)</option>
                                        <option value="Other">Other</option>
                                    </select>
                                </div>
                                <div className="flex gap-4">
                                    <div className="flex-1">
                                        <label className="block text-sm text-zinc-400 mb-1">Total Value ($)</label>
                                        <input
                                            type="number"
                                            required
                                            value={newAsset.value}
                                            onChange={e => setNewAsset({ ...newAsset, value: e.target.value })}
                                            className="w-full bg-black/50 border border-white/10 rounded-md p-2 text-white"
                                            placeholder="1500.00"
                                        />
                                    </div>
                                    <div className="w-1/3">
                                        <label className="block text-sm text-zinc-400 mb-1">Quantity</label>
                                        <input
                                            type="number"
                                            value={newAsset.quantity}
                                            onChange={e => setNewAsset({ ...newAsset, quantity: e.target.value })}
                                            className="w-full bg-black/50 border border-white/10 rounded-md p-2 text-white"
                                            placeholder="1"
                                        />
                                    </div>
                                </div>
                                <Button type="submit" className="w-full bg-emerald-500 hover:bg-emerald-600">
                                    Save Asset
                                </Button>
                            </form>
                        </DialogContent>
                    </Dialog>
                </div>

                {/* Big Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                    <Card className="glass-panel border-white/10 bg-emerald-900/10">
                        <CardContent className="pt-6">
                            <p className="text-zinc-400 text-sm font-medium uppercase tracking-wider">Net Worth</p>
                            <p className="text-4xl font-bold text-white mt-2">{formatMoney(data?.net_worth || 0)}</p>
                        </CardContent>
                    </Card>
                    <Card className="glass-panel border-white/10 bg-blue-900/10">
                        <CardContent className="pt-6">
                            <p className="text-zinc-400 text-sm font-medium uppercase tracking-wider">Total Assets</p>
                            <p className="text-4xl font-bold text-blue-400 mt-2">{formatMoney(data?.total_assets || 0)}</p>
                        </CardContent>
                    </Card>
                    <Card className="glass-panel border-white/10 bg-rose-900/10">
                        <CardContent className="pt-6">
                            <p className="text-zinc-400 text-sm font-medium uppercase tracking-wider">Total Liabilities</p>
                            <p className="text-4xl font-bold text-rose-400 mt-2">{formatMoney(data?.total_liabilities || 0)}</p>
                        </CardContent>
                    </Card>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Holdings List */}
                    <div className="lg:col-span-2 space-y-4">
                        <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                            <Wallet className="h-5 w-5 text-emerald-400" /> Holdings
                        </h3>
                        {data?.assets.length === 0 ? (
                            <div className="text-center py-12 border border-dashed border-white/10 rounded-xl text-zinc-500">
                                No assets tracked yet. Add one to get started!
                            </div>
                        ) : (
                            data?.assets.map((asset) => (
                                <motion.div
                                    key={asset.id}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="bg-zinc-900/50 border border-white/5 rounded-xl p-4 flex items-center justify-between group"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className={`p-3 rounded-full ${asset.type === 'Liability' ? 'bg-rose-500/10 text-rose-400' :
                                                asset.type === 'Crypto' ? 'bg-orange-500/10 text-orange-400' :
                                                    'bg-blue-500/10 text-blue-400'
                                            }`}>
                                            {asset.type === 'Crypto' ? <Bitcoin className="h-5 w-5" /> :
                                                asset.type === 'Real Estate' ? <Building className="h-5 w-5" /> :
                                                    <DollarSign className="h-5 w-5" />}
                                        </div>
                                        <div>
                                            <h4 className="font-semibold text-white">{asset.name}</h4>
                                            <p className="text-sm text-zinc-500">{asset.type} • {asset.quantity} units</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <span className={`text-lg font-bold ${asset.type === 'Liability' ? 'text-rose-400' : 'text-white'}`}>
                                            {asset.type === 'Liability' ? '-' : ''}{formatMoney(asset.value)}
                                        </span>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => handleDelete(asset.id)}
                                            className="opacity-0 group-hover:opacity-100 transition-opacity text-zinc-500 hover:text-red-400"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </motion.div>
                            ))
                        )}
                    </div>

                    {/* Allocation Chart */}
                    <div>
                        <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                            <TrendingUp className="h-5 w-5 text-blue-400" /> Allocation
                        </h3>
                        <Card className="glass-panel border-white/10 bg-zinc-900/50 p-6">
                            <div className="h-[250px] w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={assetDistribution}
                                            innerRadius={60}
                                            outerRadius={80}
                                            paddingAngle={5}
                                            dataKey="value"
                                        >
                                            {assetDistribution.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#18181b', borderColor: '#3f3f46', borderRadius: '8px' }}
                                            itemStyle={{ color: '#fff' }}
                                            formatter={(value: number) => formatMoney(value)}
                                        />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                            {/* Legend */}
                            <div className="grid grid-cols-2 gap-2 mt-4">
                                {assetDistribution.map((entry, index) => (
                                    <div key={index} className="flex items-center gap-2 text-sm text-zinc-400">
                                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                                        <span className="truncate">{entry.name}</span>
                                    </div>
                                ))}
                            </div>
                        </Card>
                    </div>
                </div>
            </div>
        </div>
    )
}

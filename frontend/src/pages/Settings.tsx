import { useState, useCallback, useEffect } from 'react'
import { PWAService } from '../services/pwaService'
import { aiService, AIStatus, ScanTaskStatus } from '../services/aiService'
import type { ScanStats, OrphanStats } from '../types/album'

// 获取当前使用的 GPU 名称
const getCurrentGpuName = (aiStatus: AIStatus | null): string => {
  if (!aiStatus?.model_info.loaded || !aiStatus.model_info.current_provider) {
    return '未加载'
  }
  
  const provider = aiStatus.model_info.current_provider
  const gpuProviders = aiStatus.model_info.available_providers?.gpu_providers || []
  
  // 查找对应的 GPU 名称
  const gpuInfo = gpuProviders.find(p => p.name === provider)
  if (gpuInfo) {
    return gpuInfo.display_name
  }
  
  // 回退到通用名称
  if (provider === 'CPUExecutionProvider') return 'CPU'
  return provider
}

// 图标
const RefreshIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182" />
  </svg>
)

const TrashIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
  </svg>
)

const CheckIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
  </svg>
)

const XIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
  </svg>
)

const AlertIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
  </svg>
)

const LoadingSpinner = ({ className }: { className?: string }) => (
  <svg className={`animate-spin ${className}`} fill="none" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
  </svg>
)

type ToastType = 'success' | 'error' | 'info'

interface Toast {
  id: number
  message: string
  type: ToastType
}

// 设置项组件
const SettingRow = ({ 
  label, 
  description, 
  children 
}: { 
  label: string
  description?: string
  children: React.ReactNode 
}) => (
  <div className="flex items-center justify-between py-4">
    <div>
      <div className="text-sm font-medium text-gray-900 dark:text-white">{label}</div>
      {description && <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{description}</div>}
    </div>
    <div className="flex items-center gap-2">{children}</div>
  </div>
)

// 按钮组件
const ActionButton = ({ 
  onClick, 
  loading,
  disabled,
  variant = 'primary',
  children 
}: { 
  onClick: () => void
  loading?: boolean
  disabled?: boolean
  variant?: 'primary' | 'danger'
  children: React.ReactNode 
}) => {
  const base = "px-4 py-1.5 text-xs font-medium rounded-full transition-all flex items-center gap-1.5 active:scale-95"
  const styles = variant === 'primary'
    ? `${base} bg-gray-900 dark:bg-white text-white dark:text-gray-900 hover:opacity-90`
    : `${base} bg-red-500/10 text-red-500 hover:bg-red-500/20`

  return (
    <button onClick={onClick} disabled={loading || disabled} className={`${styles} disabled:opacity-50`}>
      {loading ? <LoadingSpinner className="w-3.5 h-3.5" /> : children}
    </button>
  )
}

// 统计数值组件
const StatValue = ({ value, label }: { value: number | string, label: string }) => (
  <div className="flex items-center justify-between">
    <span className="text-xs text-gray-500 dark:text-gray-400">{label}</span>
    <span className="text-sm font-semibold text-gray-900 dark:text-white">{value}</span>
  </div>
)

const Settings = (): JSX.Element => {
  const [loading, setLoading] = useState<string | null>(null)
  const [scanStats, setScanStats] = useState<ScanStats | null>(null)
  const [orphanStats, setOrphanStats] = useState<OrphanStats | null>(null)
  const [toasts, setToasts] = useState<Toast[]>([])
  const [confirmDialog, setConfirmDialog] = useState<{
    title: string
    message: string
    onConfirm: () => void
  } | null>(null)
  const [pwaService] = useState(() => new PWAService())
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null)
  const [aiTaskStatus, setAiTaskStatus] = useState<ScanTaskStatus | null>(null)
  const [selectedProvider, setSelectedProvider] = useState<string>('')
  const [scanProgress, setScanProgress] = useState<{
    status: 'idle' | 'running' | 'completed' | 'failed'
    total: number
    processed: number
    progress: number
    current_file?: string
    new_albums: number
    updated_albums: number
  } | null>(null)

  // 加载时自动获取统计数据
  useEffect(() => {
    const loadStats = async () => {
      try {
        const [scan, orphan] = await Promise.all([
          pwaService.getScanStats(),
          pwaService.getOrphanStats()
        ])
        setScanStats(scan)
        setOrphanStats(orphan)
      } catch (e) {
        console.error('加载统计数据失败:', e)
      }
    }
    loadStats()
  }, [pwaService])

  // 检查是否有正在运行的扫描任务
  useEffect(() => {
    const checkRunningScan = async () => {
      try {
        const status = await pwaService.getScanStatus()
        if (status.is_running) {
          // 有正在运行的扫描任务，连接 SSE 获取进度
          setScanProgress({ status: 'running', total: 0, processed: 0, progress: 0, new_albums: 0, updated_albums: 0 })
          setLoading('scan')
          
          const API_BASE = import.meta.env.DEV 
            ? (import.meta.env.VITE_API_BASE || 'http://localhost:8000')
            : window.location.origin
          
          const eventSource = new EventSource(`${API_BASE}/api/scan/progress`)
          
          eventSource.onmessage = (event) => {
            try {
              const data = JSON.parse(event.data)
              
              if (data.type === 'heartbeat') return
              
              if (data.status === 'running') {
                setScanProgress({
                  status: 'running',
                  total: data.total || 0,
                  processed: data.processed || 0,
                  progress: data.progress || 0,
                  current_file: data.current_file,
                  new_albums: data.new_albums || 0,
                  updated_albums: data.updated_albums || 0
                })
              } else if (data.status === 'completed') {
                setScanProgress({
                  status: 'completed',
                  total: data.total || 0,
                  processed: data.processed || 0,
                  progress: 100,
                  new_albums: data.new_albums || 0,
                  updated_albums: data.updated_albums || 0
                })
                eventSource.close()
                setLoading(null)
                
                // 重新加载统计数据
                Promise.all([
                  pwaService.getScanStats(),
                  pwaService.getOrphanStats()
                ]).then(([scan, orphan]) => {
                  setScanStats(scan)
                  setOrphanStats(orphan)
                })
              } else if (data.status === 'failed') {
                setScanProgress({
                  status: 'failed',
                  total: 0,
                  processed: 0,
                  progress: 0,
                  new_albums: 0,
                  updated_albums: 0
                })
                eventSource.close()
                setLoading(null)
              } else if (data.status === 'no_task') {
                // 没有正在进行的任务
                setScanProgress(null)
                setLoading(null)
                eventSource.close()
              }
            } catch (e) {
              console.error('解析进度数据失败:', e)
            }
          }
          
          eventSource.onerror = () => {
            console.error('SSE 连接错误')
            eventSource.close()
            setLoading(null)
            setScanProgress(null)
          }
        }
      } catch (e) {
        console.error('检查扫描状态失败:', e)
      }
    }
    checkRunningScan()
  }, [pwaService])

  // 加载 AI 状态
  useEffect(() => {
    const loadAiStatus = async () => {
      try {
        const [status, taskStatus] = await Promise.all([
          aiService.getStatus(),
          aiService.getScanStatus()
        ])
        setAiStatus(status)
        if (taskStatus.status !== 'no_task') {
          setAiTaskStatus(taskStatus)
        }
      } catch (e) {
        console.error('加载 AI 状态失败:', e)
      }
    }
    loadAiStatus()
  }, [])

  const showToast = (message: string, type: ToastType = 'info') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3000)
  }

  const handleScan = useCallback(async () => {
    setLoading('scan')
    setScanProgress({ status: 'running', total: 0, processed: 0, progress: 0, new_albums: 0, updated_albums: 0 })
    
    try {
      const result = await pwaService.scanAlbums(false)
      
      if (result.success) {
        showToast('扫描任务已启动', 'success')
        
        // 创建 SSE 连接监听进度
        const API_BASE = import.meta.env.DEV 
          ? (import.meta.env.VITE_API_BASE || 'http://localhost:8000')
          : window.location.origin
        
        const eventSource = new EventSource(`${API_BASE}/api/scan/progress`)
        
        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            
            if (data.type === 'heartbeat') return
            
            if (data.status === 'running') {
              setScanProgress({
                status: 'running',
                total: data.total || 0,
                processed: data.processed || 0,
                progress: data.progress || 0,
                current_file: data.current_file,
                new_albums: data.new_albums || 0,
                updated_albums: data.updated_albums || 0
              })
            } else if (data.status === 'completed') {
              setScanProgress({
                status: 'completed',
                total: data.total || 0,
                processed: data.processed || 0,
                progress: 100,
                new_albums: data.new_albums || 0,
                updated_albums: data.updated_albums || 0
              })
              showToast(`扫描完成: 新增 ${data.new_albums}, 更新 ${data.updated_albums}`, 'success')
              eventSource.close()
              setLoading(null)
              
              // 重新加载统计数据
              Promise.all([
                pwaService.getScanStats(),
                pwaService.getOrphanStats()
              ]).then(([scan, orphan]) => {
                setScanStats(scan)
                setOrphanStats(orphan)
              })
            } else if (data.status === 'failed') {
              setScanProgress({
                status: 'failed',
                total: 0,
                processed: 0,
                progress: 0,
                new_albums: 0,
                updated_albums: 0
              })
              showToast(`扫描失败: ${data.error || '未知错误'}`, 'error')
              eventSource.close()
              setLoading(null)
            }
          } catch (e) {
            console.error('解析进度数据失败:', e)
          }
        }
        
        eventSource.onerror = () => {
          console.error('SSE 连接错误')
          eventSource.close()
          setLoading(null)
        }
      } else {
        showToast(result.message, 'error')
        setLoading(null)
        setScanProgress(null)
      }
    } catch (error) {
      showToast(error instanceof Error ? error.message : '扫描失败', 'error')
      setLoading(null)
      setScanProgress(null)
    }
  }, [pwaService])

  const handleCleanupDeleted = useCallback(() => {
    setConfirmDialog({
      title: '清理已删除图集',
      message: '将清理 30 天前已删除的图集数据，此操作不可撤销。',
      onConfirm: async () => {
        setConfirmDialog(null)
        setLoading('cleanupDeleted')
        try {
          const result = await pwaService.cleanupDeletedAlbums(30)
          showToast(result.message, 'success')
        } catch (error) {
          showToast(error instanceof Error ? error.message : '清理失败', 'error')
        } finally {
          setLoading(null)
        }
      }
    })
  }, [pwaService])

  const handleCleanupOrphans = useCallback(() => {
    setConfirmDialog({
      title: '清理孤儿数据',
      message: '将清理数据库中的孤立关联数据，此操作不可撤销。',
      onConfirm: async () => {
        setConfirmDialog(null)
        setLoading('cleanupOrphans')
        try {
          const result = await pwaService.cleanupOrphans()
          showToast(result.message, 'success')
        } catch (error) {
          showToast(error instanceof Error ? error.message : '清理失败', 'error')
        } finally {
          setLoading(null)
        }
      }
    })
  }, [pwaService])

  const handleAiScan = useCallback(async () => {
    setLoading('aiScan')
    try {
      const result = await aiService.startScan(true)
      if (result.success) {
        showToast('AI 扫描已启动', 'success')
        setAiTaskStatus({
          task_id: result.task_id!,
          status: 'running',
          total: aiStatus?.stats.total_albums || 0,
          processed: 0,
          failed: 0,
          progress: 0,
          message: '正在扫描...'
        })
        // 开始监听进度
        const eventSource = aiService.createScanProgressStream((data) => {
          setAiTaskStatus(data)
          if (data.status === 'completed' || data.status === 'failed') {
            eventSource.close()
            // 重新加载状态
            aiService.getStatus().then(setAiStatus)
          }
        })
      } else {
        showToast(result.message, 'error')
      }
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'AI 扫描失败', 'error')
    } finally {
      setLoading(null)
    }
  }, [aiStatus])

  const handleReloadModel = useCallback(async () => {
    setLoading('reloadModel')
    try {
      const result = await aiService.loadModel(true, selectedProvider || undefined)
      if (result.success) {
        showToast('模型已重新加载', 'success')
        setAiStatus(prev => prev ? { ...prev, model_info: result.model_info } : null)
      } else {
        showToast('模型加载失败', 'error')
      }
    } catch (error) {
      showToast(error instanceof Error ? error.message : '加载失败', 'error')
    } finally {
      setLoading(null)
    }
  }, [selectedProvider])

  return (
    <div className="min-h-screen bg-gray-50/50 dark:bg-gray-950">
      {/* Toast */}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map(toast => (
          <div
            key={toast.id}
            className={`
              flex items-center gap-2 px-4 py-2.5 backdrop-blur-xl rounded-2xl shadow-lg text-sm font-medium animate-bounce-in
              ${toast.type === 'success' ? 'bg-green-500/90 text-white' : ''}
              ${toast.type === 'error' ? 'bg-red-500/90 text-white' : ''}
              ${toast.type === 'info' ? 'bg-gray-900/90 dark:bg-white/90 text-white dark:text-gray-900' : ''}
            `}
          >
            {toast.type === 'success' && <CheckIcon className="w-4 h-4" />}
            {toast.type === 'error' && <XIcon className="w-4 h-4" />}
            {toast.message}
          </div>
        ))}
      </div>

      {/* 确认弹窗 */}
      {confirmDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="absolute inset-0 bg-black/30 backdrop-blur-md" onClick={() => setConfirmDialog(null)} />
          <div className="relative backdrop-blur-xl bg-white/80 dark:bg-gray-900/80 rounded-3xl shadow-2xl max-w-xs w-full p-6 animate-bounce-in">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center">
                <AlertIcon className="w-5 h-5 text-red-500" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white">{confirmDialog.title}</h3>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">{confirmDialog.message}</p>
            <div className="flex gap-3">
              <button
                onClick={() => setConfirmDialog(null)}
                className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-500/10 rounded-xl hover:bg-gray-500/20 transition-colors"
              >
                取消
              </button>
              <button
                onClick={confirmDialog.onConfirm}
                className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-red-500 rounded-xl hover:bg-red-600 transition-colors"
              >
                确认清理
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-xl mx-auto px-4 pt-6 pb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">设置</h1>
        <p className="text-sm text-gray-500 mb-8">扫描、统计与数据维护</p>

        {/* 统计卡片 - 毛玻璃效果 */}
        {scanStats && (
          <div className="backdrop-blur-xl bg-white/60 dark:bg-gray-900/60 rounded-3xl p-5 mb-6 space-y-3">
            <StatValue value={scanStats.total_albums} label="图集" />
            <StatValue value={scanStats.total_images} label="图片" />
            <StatValue value={scanStats.total_size_mb} label="存储大小 (MB)" />
            <StatValue value={scanStats.recent_scans_today} label="今日扫描" />
            <StatValue value={orphanStats?.total_orphans ?? 0} label="孤儿数据" />
            <div className="pt-2 border-t border-gray-200/50 dark:border-gray-700/50">
              <StatValue value={scanStats.tags} label="标签" />
            </div>
          </div>
        )}

        {/* 设置列表 - 毛玻璃效果 */}
        <div className="backdrop-blur-xl bg-white/60 dark:bg-gray-900/60 rounded-3xl px-5 divide-y divide-gray-200/50 dark:divide-gray-700/50">
          <SettingRow label="扫描图集" description="扫描并更新本地 CBZ 图集">
            <ActionButton onClick={handleScan} loading={loading === 'scan'}>
              <RefreshIcon className="w-3.5 h-3.5" />
              {scanProgress?.status === 'running' ? '扫描中' : '扫描'}
            </ActionButton>
          </SettingRow>

          {/* 图集扫描进度 */}
          {scanProgress && scanProgress.status === 'running' && (
            <div className="py-4 animate-fade-in">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  进度: {scanProgress.processed}/{scanProgress.total}
                  {scanProgress.current_file && ` - ${scanProgress.current_file}`}
                </span>
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                  {scanProgress.progress}%
                </span>
              </div>
              <div className="w-full bg-gray-200/50 dark:bg-gray-700/50 rounded-full h-1.5 overflow-hidden">
                <div 
                  className="bg-gray-900 dark:bg-white h-1.5 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${scanProgress.progress}%` }}
                />
              </div>
              <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
                <span>新增: {scanProgress.new_albums}</span>
                <span>更新: {scanProgress.updated_albums}</span>
              </div>
            </div>
          )}

          {/* 扫描完成状态 */}
          {scanProgress && scanProgress.status === 'completed' && (
            <div className="py-4 animate-fade-in">
              <div className="flex items-center justify-between text-xs">
                <span className="text-green-500 font-medium">扫描完成</span>
                <span className="text-gray-500">
                  新增 {scanProgress.new_albums} / 更新 {scanProgress.updated_albums}
                </span>
              </div>
            </div>
          )}

          {/* 扫描失败状态 */}
          {scanProgress && scanProgress.status === 'failed' && (
            <div className="py-4 animate-fade-in">
              <div className="text-xs text-red-500">扫描失败</div>
            </div>
          )}

          <SettingRow label="清理已删除" description="30 天前已删除的图集数据">
            <ActionButton onClick={handleCleanupDeleted} loading={loading === 'cleanupDeleted'} variant="danger">
              <TrashIcon className="w-3.5 h-3.5" />
              清理
            </ActionButton>
          </SettingRow>

          <SettingRow label="清理孤儿数据" description="数据库中的孤立关联数据">
            <ActionButton onClick={handleCleanupOrphans} loading={loading === 'cleanupOrphans'} variant="danger">
              <TrashIcon className="w-3.5 h-3.5" />
              清理
            </ActionButton>
          </SettingRow>


        </div>

        {/* AI 搜索设置 */}
        <div className="backdrop-blur-xl bg-white/60 dark:bg-gray-900/60 rounded-3xl px-5 divide-y divide-gray-200/50 dark:divide-gray-700/50 mt-6">
          <SettingRow 
            label="AI 向量扫描" 
            description={aiStatus?.has_model_files 
              ? `已索引 ${aiStatus?.stats.embedded_albums || 0}/${aiStatus?.stats.total_albums || 0} 图集`
              : '未找到模型文件，请先下载模型'
            }
          >
            <ActionButton 
              onClick={handleAiScan} 
              loading={loading === 'aiScan' || aiTaskStatus?.status === 'running'}
              disabled={!aiStatus?.has_model_files}
            >
              <RefreshIcon className="w-3.5 h-3.5" />
              {aiTaskStatus?.status === 'running' ? '扫描中' : '扫描'}
            </ActionButton>
          </SettingRow>

          {aiTaskStatus && aiTaskStatus.status === 'running' && (
            <div className="py-4 animate-fade-in">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  进度: {aiTaskStatus.processed}/{aiTaskStatus.total}
                </span>
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                  {aiTaskStatus.progress}%
                </span>
              </div>
              <div className="w-full bg-gray-200/50 dark:bg-gray-700/50 rounded-full h-1.5 overflow-hidden">
                <div 
                  className="bg-gray-900 dark:bg-white h-1.5 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${aiTaskStatus.progress}%` }}
                />
              </div>
            </div>
          )}

          <SettingRow 
            label="模型状态" 
            description={aiStatus?.model_info.loaded 
              ? `已加载 - ${getCurrentGpuName(aiStatus)}` 
              : aiStatus?.has_model_files 
                ? '模型文件就绪，扫描时自动加载' 
                : '未找到模型文件'
            }
          >
            <span className={`text-xs px-2 py-1 rounded-full ${
              aiStatus?.model_info.loaded 
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : aiStatus?.has_model_files
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                  : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
            }`}>
              {aiStatus?.model_info.loaded ? '已加载' : aiStatus?.has_model_files ? '待加载' : '无文件'}
            </span>
          </SettingRow>

          {/* GPU 选择 */}
          {aiStatus?.model_info.available_providers?.gpu_providers && 
           aiStatus.model_info.available_providers.gpu_providers.length > 0 && (
            <SettingRow 
              label="加速设备" 
              description="选择 GPU 或 CPU 进行推理"
            >
              <select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
                className="text-xs px-3 py-1.5 bg-gray-500/10 rounded-xl border-0 focus:ring-2 focus:ring-gray-400/30 outline-none"
              >
                <option value="">自动选择</option>
                {aiStatus.model_info.available_providers.gpu_providers.map(p => (
                  <option key={p.name} value={p.name}>{p.display_name}</option>
                ))}
                <option value="CPUExecutionProvider">CPU</option>
              </select>
              <ActionButton 
                onClick={handleReloadModel} 
                loading={loading === 'reloadModel'}
              >
                <RefreshIcon className="w-3.5 h-3.5" />
                应用
              </ActionButton>
            </SettingRow>
          )}
        </div>
      </div>
    </div>
  )
}

export default Settings

import { useState, useCallback } from 'react'
import { PWAService } from '../services/pwaService'
import type { ScanResponse, ScanStats, OrphanStats } from '../types/album'

const Settings = (): JSX.Element => {
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [scanStats, setScanStats] = useState<ScanStats | null>(null)
  const [orphanStats, setOrphanStats] = useState<OrphanStats | null>(null)
  const [pwaService] = useState(() => new PWAService())

  // 异步扫描
  const handleAsyncScan = useCallback(async () => {
    setLoading(true)
    setMessage('')
    try {
      const result = await pwaService.scanAlbums(false)
      setMessage(result.message)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '扫描失败')
    } finally {
      setLoading(false)
    }
  }, [pwaService])

  // 同步扫描
  const handleSyncScan = useCallback(async () => {
    setLoading(true)
    setMessage('')
    try {
      const result = await pwaService.scanAlbumsSync()
      setMessage(result.message)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '扫描失败')
    } finally {
      setLoading(false)
    }
  }, [pwaService])

  // 获取扫描统计
  const handleGetScanStats = useCallback(async () => {
    setLoading(true)
    setMessage('')
    try {
      const stats = await pwaService.getScanStats()
      setScanStats(stats)
      setMessage('统计信息已获取')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '获取统计失败')
    } finally {
      setLoading(false)
    }
  }, [pwaService])

  // 获取孤儿数据统计
  const handleGetOrphanStats = useCallback(async () => {
    setLoading(true)
    setMessage('')
    try {
      const stats = await pwaService.getOrphanStats()
      setOrphanStats(stats)
      setMessage('孤儿数据统计已获取')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '获取统计失败')
    } finally {
      setLoading(false)
    }
  }, [pwaService])

  // 清理已删除图集
  const handleCleanupDeleted = useCallback(async () => {
    setLoading(true)
    setMessage('')
    try {
      const result = await pwaService.cleanupDeletedAlbums(30)
      setMessage(result.message)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '清理失败')
    } finally {
      setLoading(false)
    }
  }, [pwaService])

  // 清理孤儿数据
  const handleCleanupOrphans = useCallback(async () => {
    setLoading(true)
    setMessage('')
    try {
      const result = await pwaService.cleanupOrphans()
      setMessage(result.message)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '清理失败')
    } finally {
      setLoading(false)
    }
  }, [pwaService])

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-8">设置</h1>
        
        {/* 扫描任务区域 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">扫描任务</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <button
              onClick={handleAsyncScan}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '处理中...' : '异步扫描'}
            </button>
            
            <button
              onClick={handleSyncScan}
              disabled={loading}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '处理中...' : '同步扫描'}
            </button>
          </div>

          {message && (
            <div className="mt-4 p-3 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-300">
              {message}
            </div>
          )}
        </div>

        {/* 统计信息区域 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">统计信息</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <button
              onClick={handleGetScanStats}
              disabled={loading}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '处理中...' : '获取扫描统计'}
            </button>
            
            <button
              onClick={handleGetOrphanStats}
              disabled={loading}
              className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '处理中...' : '获取孤儿数据统计'}
            </button>
          </div>

          {scanStats && (
            <div className="mt-4 p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
              <h3 className="font-medium text-gray-900 dark:text-white mb-2">扫描统计</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                <div>
                  <span className="text-gray-500 dark:text-gray-400">总图集:</span>
                  <span className="ml-1 font-medium text-gray-900 dark:text-white">{scanStats.total_albums}</span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">总图片:</span>
                  <span className="ml-1 font-medium text-gray-900 dark:text-white">{scanStats.total_images}</span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">总大小:</span>
                  <span className="ml-1 font-medium text-gray-900 dark:text-white">{scanStats.total_size_mb} MB</span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">今日扫描:</span>
                  <span className="ml-1 font-medium text-gray-900 dark:text-white">{scanStats.recent_scans_today}</span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">套图:</span>
                  <span className="ml-1 font-medium text-gray-900 dark:text-white">{scanStats.organizations}</span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">模特:</span>
                  <span className="ml-1 font-medium text-gray-900 dark:text-white">{scanStats.models}</span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">标签:</span>
                  <span className="ml-1 font-medium text-gray-900 dark:text-white">{scanStats.tags}</span>
                </div>
              </div>
            </div>
          )}

          {orphanStats && (
            <div className="mt-4 p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
              <h3 className="font-medium text-gray-900 dark:text-white mb-2">孤儿数据统计</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                <div>
                  <span className="text-gray-500 dark:text-gray-400">孤儿标签关联:</span>
                  <span className="ml-1 font-medium text-gray-900 dark:text-white">{orphanStats.orphaned_album_tags}</span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">孤立标签:</span>
                  <span className="ml-1 font-medium text-gray-900 dark:text-white">{orphanStats.orphan_tags}</span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">孤立套图:</span>
                  <span className="ml-1 font-medium text-gray-900 dark:text-white">{orphanStats.orphan_orgs}</span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">孤立模特:</span>
                  <span className="ml-1 font-medium text-gray-900 dark:text-white">{orphanStats.orphan_models}</span>
                </div>
                <div className="col-span-2 md:col-span-4">
                  <span className="text-gray-500 dark:text-gray-400">总计:</span>
                  <span className="ml-1 font-medium text-red-600 dark:text-red-400">{orphanStats.total_orphans}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 清理数据区域 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">数据清理</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={handleCleanupDeleted}
              disabled={loading}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '处理中...' : '清理已删除图集(30天)'}
            </button>
            
            <button
              onClick={handleCleanupOrphans}
              disabled={loading}
              className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '处理中...' : '清理孤儿数据'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Settings

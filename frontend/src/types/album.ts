export interface Album {
  id: string
  title: string
  description: string
  coverImage: string
  imageCount: number
}

export interface ImageItem {
  id: string
  url: string
  title: string
  description: string
}

export interface ZoomState {
  level: number
  offset: { x: number; y: number }
}

export interface TouchState {
  start: { x: number; y: number; time: number } | null
  startDistance: number
  startZoom: number
  isMoving: boolean
}

export interface DragState {
  isDragging: boolean
  start: { x: number; y: number }
}

// 新增：后端分类数据类型
export interface Organization {
  id: number
  name: string
  description?: string
  album_count: number
  cover_url?: string
  created_at: string
}

export interface Model {
  id: number
  name: string
  description?: string
  album_count: number
  cover_url?: string
  created_at: string
}

export interface Tag {
  id: number
  name: string
  type: string
  description?: string
  album_count: number
  created_at: string
}

export interface CategoryTree {
  org: Organization[]
  model: Model[]
  tag: Tag[]
}

// 新增：图集相关类型
export interface AlbumSummary {
  id: number
  title: string
  cover_url: string
  image_count: number
  tags: string[]
  description?: string
}

export interface PagedResponse {
  total: number
  page: number
  size: number
  items: AlbumSummary[]
}

// 前端使用的图集卡片数据类型
export interface AlbumCard {
  id: string
  title: string
  description: string
  coverImage: string
  imageCount: number
}

// 前端使用的图集详情数据类型
export interface Album {
  id: string
  title: string
  description: string
  coverImage: string
  imageCount: number
  tags: Tag[]
}

// 后端图集详情响应类型
export interface AlbumDetailResponse {
  id: number
  title: string
  file_path: string
  file_name: string
  description?: string
  image_count?: number
  cover_image?: string
  file_size?: number
  created_at: string
  updated_at: string
  tags: Tag[]
}

// 后端图片列表响应类型（支持分页）
export interface AlbumImagesResponse {
  album_id: number
  total: number
  page: number
  size: number
  has_more: boolean
  images: Array<{
    name: string
    url: string
  }>
}

// 后端标签响应类型
export interface TagResponse {
  id: number
  name: string
  type: string
  description?: string
  album_count: number
  created_at: string
}

// 扫描响应类型
export interface ScanResponse {
  success: boolean
  message: string
  scanned_files: number
  new_albums: number
  updated_albums: number
}

// 扫描统计信息类型
export interface ScanStats {
  total_albums: number
  total_images: number
  total_size_mb: number
  recent_scans_today: number
  organizations: number
  models: number
  tags: number
}

// 孤儿数据统计类型
export interface OrphanStats {
  orphaned_album_tags: number
  orphan_tags: number
  orphan_orgs: number
  orphan_models: number
  total_orphans: number
}
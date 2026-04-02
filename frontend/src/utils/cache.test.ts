/**
 * SessionState 工具函数测试
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { sessionState, CacheKeys } from './cache'

describe('SessionState', () => {
  beforeEach(() => {
    // 每个测试前清空状态
    sessionState.clear()
  })

  it('should set and get state', () => {
    sessionState.set('key', 'value')
    expect(sessionState.get('key')).toBe('value')
  })

  it('should return null for non-existent key', () => {
    expect(sessionState.get('nonexistent')).toBeNull()
  })

  it('should delete state', () => {
    sessionState.set('key', 'value')
    sessionState.delete('key')
    expect(sessionState.get('key')).toBeNull()
  })

  it('should clear all states', () => {
    sessionState.set('key1', 'value1')
    sessionState.set('key2', 'value2')
    sessionState.clear()
    expect(sessionState.get('key1')).toBeNull()
    expect(sessionState.get('key2')).toBeNull()
  })

  it('should check if key exists', () => {
    sessionState.set('key', 'value')
    expect(sessionState.has('key')).toBe(true)
    expect(sessionState.has('nonexistent')).toBe(false)
  })

  it('should handle complex objects', () => {
    const complexObject = {
      albums: [1, 2, 3],
      page: 1,
      filters: { type: 'org' }
    }
    sessionState.set('complex', complexObject)
    expect(sessionState.get('complex')).toEqual(complexObject)
  })
})

describe('CacheKeys', () => {
  it('should generate albums state key', () => {
    const key = CacheKeys.state.albums('org', 1)
    expect(key).toBe('state:albums:org:1:none')
  })

  it('should generate albums state key with search', () => {
    const key = CacheKeys.state.albums('org', 1, 'test')
    expect(key).toBe('state:albums:org:1:test')
  })

  it('should generate albums state key with null values', () => {
    const key = CacheKeys.state.albums(null, null)
    expect(key).toBe('state:albums:all:all:none')
  })

  it('should generate album detail state key', () => {
    const key = CacheKeys.state.albumDetail('123')
    expect(key).toBe('state:album:123')
  })
})

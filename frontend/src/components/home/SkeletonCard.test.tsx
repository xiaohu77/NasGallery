/**
 * SkeletonCard 组件测试
 */
import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { SkeletonCard } from './SkeletonCard'

describe('SkeletonCard', () => {
  it('should render without crashing', () => {
    const { container } = render(<SkeletonCard />)
    expect(container).toBeInTheDocument()
  })

  it('should have animate-pulse class', () => {
    const { container } = render(<SkeletonCard />)
    expect(container.firstChild).toHaveClass('animate-pulse')
  })

  it('should contain loading spinner', () => {
    const { container } = render(<SkeletonCard />)
    const spinner = container.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
  })
})

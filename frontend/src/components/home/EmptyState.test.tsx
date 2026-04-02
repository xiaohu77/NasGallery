/**
 * EmptyState 组件测试
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { EmptyState } from './EmptyState'

describe('EmptyState', () => {
  it('should render default title', () => {
    render(<EmptyState />)
    expect(screen.getByText('暂无数据')).toBeInTheDocument()
  })

  it('should render custom title', () => {
    render(<EmptyState title="No Albums" />)
    expect(screen.getByText('No Albums')).toBeInTheDocument()
  })

  it('should render description when provided', () => {
    render(<EmptyState description="Try adding some albums" />)
    expect(screen.getByText('Try adding some albums')).toBeInTheDocument()
  })

  it('should render icon when provided', () => {
    const icon = <span data-testid="test-icon">Icon</span>
    render(<EmptyState icon={icon} />)
    expect(screen.getByTestId('test-icon')).toBeInTheDocument()
  })

  it('should not render description when not provided', () => {
    const { container } = render(<EmptyState />)
    const description = container.querySelector('p')
    expect(description).not.toBeInTheDocument()
  })
})

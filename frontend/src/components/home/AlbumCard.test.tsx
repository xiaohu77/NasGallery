/**
 * AlbumCard 组件测试
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AlbumCard } from './AlbumCard'

const mockAlbum = {
  id: '1',
  title: 'Test Album',
  description: 'Test Description',
  coverImage: 'http://example.com/cover.jpg',
  imageCount: 10
}

describe('AlbumCard', () => {
  it('should render album title', () => {
    render(
      <MemoryRouter>
        <AlbumCard album={mockAlbum} />
      </MemoryRouter>
    )
    expect(screen.getByText('Test Album')).toBeInTheDocument()
  })

  it('should render album description', () => {
    render(
      <MemoryRouter>
        <AlbumCard album={mockAlbum} />
      </MemoryRouter>
    )
    expect(screen.getByText('Test Description')).toBeInTheDocument()
  })

  it('should show image count', () => {
    render(
      <MemoryRouter>
        <AlbumCard album={mockAlbum} />
      </MemoryRouter>
    )
    expect(screen.getByText('10 张')).toBeInTheDocument()
  })

  it('should show "无封面" when no cover image', () => {
    render(
      <MemoryRouter>
        <AlbumCard album={{ ...mockAlbum, coverImage: '' }} />
      </MemoryRouter>
    )
    expect(screen.getByText('无封面')).toBeInTheDocument()
  })

  it('should show similarity when provided', () => {
    render(
      <MemoryRouter>
        <AlbumCard album={mockAlbum} similarity={0.85} />
      </MemoryRouter>
    )
    expect(screen.getByText('85%')).toBeInTheDocument()
  })

  it('should call onClick when clicked', () => {
    const onClick = vi.fn()
    render(
      <MemoryRouter>
        <AlbumCard album={mockAlbum} onClick={onClick} />
      </MemoryRouter>
    )
    
    fireEvent.click(screen.getByRole('link'))
    expect(onClick).toHaveBeenCalled()
  })

  it('should link to album detail page', () => {
    render(
      <MemoryRouter>
        <AlbumCard album={mockAlbum} />
      </MemoryRouter>
    )
    
    const link = screen.getByRole('link')
    expect(link).toHaveAttribute('href', '/album/1')
  })

  it('should render cover image with correct src', () => {
    render(
      <MemoryRouter>
        <AlbumCard album={mockAlbum} />
      </MemoryRouter>
    )
    
    const img = screen.getByRole('img')
    expect(img).toHaveAttribute('src', 'http://example.com/cover.jpg')
    expect(img).toHaveAttribute('alt', 'Test Album')
  })

  it('should not render description when empty', () => {
    render(
      <MemoryRouter>
        <AlbumCard album={{ ...mockAlbum, description: '' }} />
      </MemoryRouter>
    )
    
    expect(screen.queryByText('Test Description')).not.toBeInTheDocument()
  })
})

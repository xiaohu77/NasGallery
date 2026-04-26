import React, { useEffect, ReactNode } from 'react';
import { useLocation } from 'react-router-dom';

interface KeepAliveProps {
  children: ReactNode;
  name: string;
}

/**
 * KeepAlive 组件
 * 用于保持组件状态，避免路由切换时重新挂载
 */
export const KeepAlive: React.FC<KeepAliveProps> = ({ children, name }) => {
  const location = useLocation();
  const activeKeyRef = React.useRef<string>('');

  // 生成当前路径的唯一标识
  const getKey = () => {
    return `${name}:${location.pathname}`;
  };

  // 获取当前激活的key
  const activeKey = getKey();

  // 当路径变化时，检查是否需要恢复状态
  useEffect(() => {
    // 如果是同一个组件但不同路径，或者从详情页返回
    if (activeKeyRef.current && activeKey !== activeKeyRef.current) {
      // 可以在这里处理状态保存逻辑
    }

    activeKeyRef.current = activeKey;
  }, [activeKey]);

  return (
    <div data-keep-alive={name} data-key={activeKey}>
      {children}
    </div>
  );
};

/**
 * 创建 KeepAlive 包装器
 */
export function withKeepAlive<P extends object>(
  Component: React.ComponentType<P>,
  name: string
): React.FC<P> {
  return (props: P) => (
    <KeepAlive name={name}>
      <Component {...props} />
    </KeepAlive>
  );
}

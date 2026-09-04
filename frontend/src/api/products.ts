import type { Product, ProductInput, ProductListResponse, ProductQuery } from '../types/product'
import { apiClient } from './client'

export async function getProducts(query: ProductQuery): Promise<ProductListResponse> {
  const response = await apiClient.get<ProductListResponse>('/products', { params: query })
  return response.data
}

export async function getProductCategories(): Promise<string[]> {
  const response = await apiClient.get<string[]>('/products/categories')
  return response.data
}

export async function createProduct(input: ProductInput): Promise<Product> {
  const response = await apiClient.post<Product>('/products', input)
  return response.data
}

export async function updateProduct(productId: number, input: ProductInput): Promise<Product> {
  const response = await apiClient.put<Product>(`/products/${productId}`, input)
  return response.data
}

export async function deactivateProduct(productId: number): Promise<void> {
  await apiClient.delete(`/products/${productId}`)
}


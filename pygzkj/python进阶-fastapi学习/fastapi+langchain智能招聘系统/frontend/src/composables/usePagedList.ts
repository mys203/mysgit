import { reactive, ref } from 'vue'
import type { PageQuery, PaginatedData } from '@/types/common'
import { getErrorMessage } from '@/utils/error'

export function usePagedList<
  TItem,
  TFilters extends Record<string, unknown>,
>(
  fetcher: (query: TFilters & PageQuery) => Promise<PaginatedData<TItem>>,
  initialFilters: TFilters,
) {
  const items = ref<TItem[]>([]) as { value: TItem[] }
  const loading = ref(false)
  const errorMessage = ref('')
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const filters = reactive({ ...initialFilters }) as TFilters

  async function load(): Promise<void> {
    loading.value = true
    errorMessage.value = ''

    try {
      const result = await fetcher({
        ...filters,
        page: page.value,
        page_size: pageSize.value,
      })
      items.value = result.items
      total.value = result.total
    } catch (error) {
      errorMessage.value = getErrorMessage(error)
      items.value = []
      total.value = 0
    } finally {
      loading.value = false
    }
  }

  function search(): void {
    page.value = 1
    void load()
  }

  function reset(): void {
    Object.assign(filters, initialFilters)
    page.value = 1
    void load()
  }

  function changePage(nextPage: number): void {
    page.value = nextPage
    void load()
  }

  function changePageSize(nextPageSize: number): void {
    pageSize.value = nextPageSize
    page.value = 1
    void load()
  }

  return {
    items,
    loading,
    errorMessage,
    total,
    page,
    pageSize,
    filters,
    load,
    search,
    reset,
    changePage,
    changePageSize,
  }
}

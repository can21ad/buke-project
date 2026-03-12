import sys
sys.path.insert(0, 'd:/怖客/scripts')
from vector_manager import VectorManager
from search_service import SearchService

# 连接数据库
vm = VectorManager('./chroma_db', 'ghost_story_video_collection', 'paraphrase-multilingual-MiniLM-L12-v2', 32)
vm.connect_db()

# 加载模型
vm.load_model()

# 创建搜索服务
ss = SearchService(vm.db_manager, vm.embedding_processor)

# 测试检索
print("\n测试语义检索（余弦相似度）：\n")
results = ss.search('医院灵异事件', top_n=3)
for r in results:
    sim = r['similarity']
    title = r['metadata'].get('title', '')[:40]
    print(f"相似度: {sim:.4f} | 标题: {title}")

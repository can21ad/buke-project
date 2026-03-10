// 清除访客统计模拟数据
// 运行此脚本清除localStorage中的模拟数据

const clearMockData = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('buke_visitor_stats');
    localStorage.removeItem('buke_mock_data_added');
    localStorage.removeItem('buke_visitor_records');
    console.log('已清除访客统计模拟数据');
  }
};

clearMockData();
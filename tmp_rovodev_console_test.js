// 在瀏覽器Console中執行的測試代碼
// 請先登入主應用 (http://localhost:4200)，然後在同一個分頁的Console中執行

console.log('🔍 開始API數據結構測試...');

// 獲取並解密token
function getToken() {
    try {
        const encryptedToken = localStorage.getItem('token');
        if (!encryptedToken) {
            console.error('❌ 未找到token，請先登入');
            return null;
        }
        
        // 使用CryptoJS解密（如果可用）
        if (typeof CryptoJS !== 'undefined') {
            const decryptedToken = CryptoJS.AES.decrypt(encryptedToken, 'phegon-dev-inventory').toString(CryptoJS.enc.Utf8);
            console.log('✅ Token解密成功');
            return decryptedToken;
        } else {
            console.log('⚠️ CryptoJS不可用，嘗試使用原始token');
            return encryptedToken;
        }
    } catch (error) {
        console.error('❌ Token處理錯誤:', error);
        return null;
    }
}

// 測試API
async function testAPI() {
    const token = getToken();
    if (!token) return;

    try {
        console.log('📡 正在請求API...');
        
        const response = await fetch('http://localhost:5050/api/transactions/all', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('✅ API請求成功！');
        
        // 分析數據
        analyzeData(data);
        
    } catch (error) {
        console.error('❌ API請求失敗:', error);
        console.log('🔧 請檢查：');
        console.log('1. 後端服務是否在 localhost:5050 運行');
        console.log('2. 是否已正確登入');
        console.log('3. CORS設置是否正確');
    }
}

// 分析數據結構
function analyzeData(transactions) {
    console.log('\n📊 === 數據分析結果 ===');
    console.log(`總交易數: ${transactions.length}`);
    
    // 按類型分組
    const sellTransactions = transactions.filter(t => t.transactionType === 'SELL');
    const purchaseTransactions = transactions.filter(t => t.transactionType === 'PURCHASE');
    
    console.log(`銷售交易: ${sellTransactions.length}`);
    console.log(`採購交易: ${purchaseTransactions.length}`);
    
    if (sellTransactions.length === 0) {
        console.log('⚠️ 沒有找到銷售交易數據');
        return;
    }
    
    // 分析客戶數據
    console.log('\n👥 === 客戶數據分析 ===');
    const sellWithCustomer = sellTransactions.filter(t => t.customer);
    const sellWithCustomerCode = sellTransactions.filter(t => t.customer?.customerCode);
    const sellWithCustomerName = sellTransactions.filter(t => t.customer?.customerName);
    
    console.log(`有客戶物件的銷售交易: ${sellWithCustomer.length}/${sellTransactions.length}`);
    console.log(`有客戶編號的銷售交易: ${sellWithCustomerCode.length}/${sellTransactions.length}`);
    console.log(`有客戶名稱的銷售交易: ${sellWithCustomerName.length}/${sellTransactions.length}`);
    
    // 分析產品數據
    console.log('\n📦 === 產品數據分析 ===');
    const sellWithProducts = sellTransactions.filter(t => t.products && t.products.length > 0);
    console.log(`有產品陣列的銷售交易: ${sellWithProducts.length}/${sellTransactions.length}`);
    
    let productAssociationsWithDetails = 0;
    let productAssociationsWithCode = 0;
    let productAssociationsWithName = 0;
    let productAssociationsWithUnitPrice = 0;
    let productAssociationsWithLineTotal = 0;
    
    sellTransactions.forEach(t => {
        if (t.products && t.products.length > 0) {
            t.products.forEach(p => {
                if (p.product) productAssociationsWithDetails++;
                if (p.product?.productCode) productAssociationsWithCode++;
                if (p.product?.productName) productAssociationsWithName++;
                if (p.unit_price !== undefined) productAssociationsWithUnitPrice++;
                if (p.line_total !== undefined) productAssociationsWithLineTotal++;
            });
        }
    });
    
    console.log(`產品關聯有詳細資訊: ${productAssociationsWithDetails}`);
    console.log(`產品關聯有產品編號: ${productAssociationsWithCode}`);
    console.log(`產品關聯有產品名稱: ${productAssociationsWithName}`);
    console.log(`產品關聯有單價: ${productAssociationsWithUnitPrice}`);
    console.log(`產品關聯有小計: ${productAssociationsWithLineTotal}`);
    
    // 顯示範例數據
    console.log('\n📋 === 範例數據 ===');
    if (sellTransactions.length > 0) {
        const sample = sellTransactions[0];
        console.log('第一筆銷售交易:');
        console.log({
            id: sample.id,
            transactionType: sample.transactionType,
            totalPrice: sample.totalPrice,
            customer: sample.customer,
            products: sample.products?.slice(0, 1), // 只顯示第一個產品
            user: sample.user
        });
    }
    
    // 檢查問題
    console.log('\n🔍 === 問題診斷 ===');
    if (sellWithCustomer.length === 0) {
        console.log('❌ 問題：所有銷售交易都沒有客戶資訊');
    }
    if (productAssociationsWithDetails === 0) {
        console.log('❌ 問題：所有產品關聯都沒有產品詳細資訊');
    }
    if (productAssociationsWithUnitPrice === 0) {
        console.log('❌ 問題：所有產品關聯都沒有單價資訊');
    }
    
    console.log('\n✅ 測試完成！');
}

// 執行測試
testAPI();
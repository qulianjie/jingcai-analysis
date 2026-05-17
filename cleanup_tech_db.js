// 清理技术学习日报重复条目 - 修复版
const https = require('https');
const API_KEY = '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';
const DS_ID = '2643200f-de7e-47e5-a84a-a31a69257824';

function notionRequest(method, endpoint, data) {
    return new Promise((resolve, reject) => {
        const body = data ? JSON.stringify(data) : null;
        const req = https.request({
            hostname: 'api.notion.com',
            path: endpoint,
            method,
            headers: {
                'Authorization': 'Bearer ' + API_KEY,
                'Notion-Version': '2025-09-03',
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(body || ''),
            },
        }, res => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                try { resolve({ status: res.statusCode, data: JSON.parse(d) }); }
                catch(e) { resolve({ status: res.statusCode, data: d }); }
            });
        });
        req.on('error', reject);
        if (body) req.write(body);
        req.end();
    });
}

function getPropValue(props, key) {
    const prop = props[key];
    if (!prop) return '';
    if (prop.title?.[0]?.plain_text) return prop.title[0].plain_text;
    if (prop.rich_text?.[0]?.plain_text) return prop.rich_text[0].plain_text;
    if (prop.select?.name) return prop.select.name;
    return '';
}

function findPropKey(props, keywords) {
    for (const k of Object.keys(props)) {
        for (const kw of keywords) {
            if (k.toLowerCase().includes(kw.toLowerCase())) return k;
        }
    }
    return null;
}

async function main() {
    console.log('📊 清理技术学习日报重复条目\n');
    
    // 1. 获取所有条目
    console.log('[1/4] 获取所有条目...');
    const { data } = await notionRequest('POST', `/v1/data_sources/${DS_ID}/query`, { page_size: 100 });
    const pages = data.results || [];
    console.log(`共 ${pages.length} 条\n`);
    
    // 2. 找到Name属性
    if (pages.length === 0) {
        console.log('没有数据');
        return;
    }
    
    const firstProps = pages[0].properties;
    console.log('属性列表:', Object.keys(firstProps).join(', '));
    
    const nameKey = findPropKey(firstProps, ['Name', 'name', '名称']);
    if (!nameKey) {
        console.log('未找到Name属性');
        return;
    }
    console.log(`Name属性: ${nameKey}\n`);
    
    // 3. 按Name分组
    console.log('[2/4] 分析重复...');
    const byName = {};
    pages.forEach(p => {
        const name = getPropValue(p.properties, nameKey);
        if (!name) return;
        if (!byName[name]) byName[name] = [];
        byName[name].push(p);
    });
    
    let toDelete = [];
    let kept = [];
    for (const [name, group] of Object.entries(byName)) {
        if (group.length <= 1) {
            kept.push(name);
            continue;
        }
        // 按属性数量排序，保留最完整的
        group.sort((a, b) => {
            const scoreA = Object.keys(a.properties || {}).filter(k => {
                const v = a.properties[k];
                return v?.title?.[0]?.plain_text || v?.rich_text?.[0]?.plain_text || v?.select?.name;
            }).length;
            const scoreB = Object.keys(b.properties || {}).filter(k => {
                const v = b.properties[k];
                return v?.title?.[0]?.plain_text || v?.rich_text?.[0]?.plain_text || v?.select?.name;
            }).length;
            return scoreB - scoreA;
        });
        
        kept.push(name);
        console.log(`\n⚠️ "${name}" - ${group.length} 条重复`);
        for (let i = 0; i < group.length; i++) {
            const score = Object.keys(group[i].properties || {}).filter(k => {
                const v = group[i].properties[k];
                return v?.title?.[0]?.plain_text || v?.rich_text?.[0]?.plain_text || v?.select?.name;
            }).length;
            console.log(`  ${i === 0 ? '✅保留' : '❌删除'} [${score}属性] ${group[i].id.substring(0, 12)}...`);
            if (i > 0) {
                toDelete.push({ id: group[i].id, name });
            }
        }
    }
    
    console.log(`\n✅ 保留: ${kept.length} 条`);
    console.log(`❌ 待删除: ${toDelete.length} 条\n`);
    
    if (toDelete.length === 0) {
        console.log('没有重复需要清理');
        return;
    }
    
    // 4. 删除重复条目
    console.log('[3/4] 删除重复条目...');
    let deleted = 0;
    for (const item of toDelete) {
        const result = await notionRequest('PATCH', `/v1/pages/${item.id}`, { archived: true });
        if (result.status === 200) {
            deleted++;
            console.log(`  ✅ 已删除: ${item.name}`);
        } else {
            console.log(`  ❌ 删除失败: ${item.name} - ${result.status}`);
        }
        await new Promise(r => setTimeout(r, 200));
    }
    
    console.log(`\n[4/4] 完成！删除了 ${deleted}/${toDelete.length} 条重复`);
}

main().catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
});

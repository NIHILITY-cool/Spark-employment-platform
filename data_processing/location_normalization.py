"""Shared location and salary rules for the employment data pipelines."""

from __future__ import annotations

import re


PROVINCE_LEVEL_LOCATIONS = frozenset({
    "安徽", "福建", "甘肃", "广东", "广西", "贵州", "海南", "河北", "黑龙江", "河南", "湖北",
    "湖南", "吉林", "江苏", "江西", "辽宁", "内蒙古", "宁夏", "青海", "山东", "山西", "陕西",
    "四川", "西藏", "新疆", "云南", "浙江", "香港", "澳门", "台湾", "全国",
})
DIRECT_CONTROLLED_CITIES = frozenset({"北京", "天津", "上海", "重庆"})
UNKNOWN_CITY = "地点待定"

# The upstream sites use this field for cities, provinces, districts and sometimes
# free-form recruiting copy. Keep a controlled catalog so only real city-level
# locations participate in the city filter and market statistics.
CANONICAL_CITIES = frozenset("""
北京 天津 上海 重庆
石家庄 唐山 秦皇岛 邯郸 邢台 保定 张家口 承德 沧州 廊坊 衡水 定州 辛集
太原 大同 阳泉 长治 晋城 朔州 晋中 运城 忻州 临汾 吕梁 古交
呼和浩特 包头 乌海 赤峰 通辽 鄂尔多斯 呼伦贝尔 巴彦淖尔 乌兰察布 霍林郭勒 满洲里 牙克石 扎兰屯 根河 额尔古纳 丰镇
沈阳 大连 鞍山 抚顺 本溪 丹东 锦州 营口 阜新 辽阳 盘锦 铁岭 朝阳 葫芦岛
长春 吉林 四平 辽源 通化 白山 松原 白城 延边 珲春
哈尔滨 齐齐哈尔 鸡西 鹤岗 双鸭山 大庆 伊春 佳木斯 七台河 牡丹江 黑河 绥化 北安 五大连池 密山 虎林 铁力 同江 富锦 绥芬河 海林 宁安 穆棱 东宁 抚远 尚志 五常 讷河 安达 肇东 海伦
南京 无锡 徐州 常州 苏州 南通 连云港 淮安 盐城 扬州 镇江 泰州 宿迁 昆山 江阴 宜兴 张家港 常熟 太仓 溧阳 扬中 句容 丹阳 高邮 仪征 兴化 靖江 泰兴 如皋 启东 海安 东台 邳州 新沂
杭州 宁波 温州 嘉兴 湖州 绍兴 金华 衢州 舟山 台州 丽水 建德 慈溪 余姚 平湖 海宁 桐乡 诸暨 嵊州 兰溪 义乌 东阳 永康 江山 临海 温岭 龙泉
合肥 芜湖 蚌埠 淮南 马鞍山 淮北 铜陵 安庆 黄山 滁州 阜阳 宿州 六安 亳州 池州 宣城 桐城 潜山 界首 天长 明光
福州 厦门 莆田 三明 泉州 漳州 南平 龙岩 宁德 福清 长乐 永安 石狮 晋江 南安 龙海 漳平 福安 福鼎 邵武 武夷山 建瓯 建阳
南昌 景德镇 萍乡 九江 新余 鹰潭 赣州 吉安 宜春 抚州 上饶 瑞昌 共青城 庐山 乐平 瑞金 龙南 井冈山 丰城 樟树 高安 贵溪 德兴
济南 青岛 淄博 枣庄 东营 烟台 潍坊 济宁 泰安 威海 日照 临沂 德州 聊城 滨州 菏泽 莱芜 胶州 平度 莱西 滕州 龙口 莱阳 莱州 蓬莱 招远 栖霞 海阳 青州 诸城 寿光 安丘 高密 昌邑 曲阜 邹城 新泰 肥城 荣成 乳山 乐陵 禹城 临清
郑州 开封 洛阳 平顶山 安阳 鹤壁 新乡 焦作 濮阳 许昌 漯河 三门峡 南阳 商丘 信阳 周口 驻马店 济源 巩义 荥阳 新密 新郑 登封 偃师 孟州 沁阳 卫辉 辉县 长垣 林州 禹州 长葛 义马 灵宝 邓州 永城 汝州 项城
武汉 黄石 十堰 宜昌 襄阳 鄂州 荆门 孝感 荆州 黄冈 咸宁 随州 恩施 仙桃 潜江 天门 丹江口 宜都 当阳 枝江 老河口 枣阳 宜城 钟祥 应城 安陆 汉川 石首 洪湖 松滋 麻城 武穴 赤壁 广水 利川
长沙 株洲 湘潭 衡阳 邵阳 岳阳 常德 张家界 益阳 郴州 永州 怀化 娄底 湘西 浏阳 宁乡 醴陵 湘乡 韶山 耒阳 常宁 武冈 汨罗 临湘 津市 沅江 资兴 洪江 冷水江 涟源 吉首
广州 韶关 深圳 珠海 汕头 佛山 江门 湛江 茂名 肇庆 惠州 梅州 汕尾 河源 阳江 清远 东莞 中山 潮州 揭阳 云浮 乐昌 南雄 台山 开平 鹤山 恩平 廉江 雷州 吴川 高州 化州 信宜 四会 兴宁 陆丰 阳春 英德 连州 普宁 罗定
南宁 柳州 桂林 梧州 北海 防城港 钦州 贵港 玉林 百色 贺州 河池 来宾 崇左 岑溪 东兴 桂平 北流 宜州 合山 凭祥
海口 三亚 三沙 儋州 五指山 琼海 文昌 万宁 东方
成都 自贡 攀枝花 泸州 德阳 绵阳 广元 遂宁 内江 乐山 南充 眉山 宜宾 广安 达州 雅安 巴中 资阳 阿坝 甘孜 凉山 都江堰 彭州 邛崃 崇州 简阳 江油 广汉 什邡 绵竹 阆中 华蓥 万源 西昌 康定 马尔康
贵阳 六盘水 遵义 安顺 毕节 铜仁 黔西南 黔东南 黔南 清镇 赤水 仁怀 凯里 都匀 福泉 兴义 兴仁
昆明 曲靖 玉溪 保山 昭通 丽江 普洱 临沧 楚雄 红河 文山 西双版纳 大理 德宏 怒江 迪庆 安宁 宣威 腾冲 水富 个旧 开远 蒙自 弥勒 景洪 瑞丽 芒市
拉萨 日喀则 昌都 林芝 山南 那曲
西安 铜川 宝鸡 咸阳 渭南 延安 汉中 榆林 安康 商洛 兴平 韩城 华阴
兰州 嘉峪关 金昌 白银 天水 武威 张掖 平凉 酒泉 庆阳 定西 陇南 临夏 甘南 玉门 敦煌
西宁 海东
银川 石嘴山 吴忠 固原 中卫 灵武 青铜峡
乌鲁木齐 克拉玛依 吐鲁番 哈密 昌吉 博州 巴州 阿克苏 克州 喀什 和田 伊犁 塔城 阿勒泰 石河子 阿拉尔 图木舒克 五家渠 北屯 铁门关 双河 可克达拉 昆玉 胡杨河 新星
香港 澳门
""".split())
PROVINCE_PREFIXES = tuple(sorted((
    "内蒙古自治区", "广西壮族自治区", "宁夏回族自治区", "新疆维吾尔自治区", "西藏自治区",
    "香港特别行政区", "澳门特别行政区", "黑龙江省", "广东省", "山东省", "四川省", "河北省", "河南省",
    "云南省", "辽宁省", "湖南省", "安徽省", "湖北省", "浙江省", "江苏省", "福建省", "江西省",
    "陕西省", "山西省", "贵州省", "甘肃省", "青海省", "吉林省", "海南省", "台湾省",
), key=len, reverse=True))
PROVINCE_ALIASES = {
    "内蒙古自治区": "内蒙古", "广西壮族自治区": "广西", "宁夏回族自治区": "宁夏", "新疆维吾尔自治区": "新疆",
    "西藏自治区": "西藏", "香港特别行政区": "香港", "澳门特别行政区": "澳门",
}
LOCATION_LABEL_RE = re.compile(r"(?:工作地点|工作地址|办公地点|上班地点|岗位地点|工作地区)\s*(?:为|在|是)?\s*[:：]?\s*([^\n\r。；;]{1,80})")
CITY_IN_LOCATION_RE = re.compile(r"(?:^|[省区、，,;；\s])([\u4e00-\u9fff]{2,8})市")
ZHILIAN_SALARY_RE = re.compile(r"(?P<lower>\d+(?:\.\d+)?)\s*-\s*(?P<upper>\d+(?:\.\d+)?)\s*(?P<unit>万|元|[Kk])")


def clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\u3000", " ")).strip()


def normalize_city_name(value: object) -> str:
    text = clean_text(value)
    if text == "中国":
        return "全国"
    text = text.removesuffix("市")
    if text in PROVINCE_ALIASES:
        return PROVINCE_ALIASES[text]
    if text.endswith("省"):
        if len(text) > 2:
            text = text.removesuffix("省")
        else:
            return text
    for prefix in PROVINCE_PREFIXES:
        if text.startswith(prefix) and len(text) > len(prefix):
            text = text[len(prefix):]
            break
    return text


def is_province_level(value: object) -> bool:
    return normalize_city_name(value) in PROVINCE_LEVEL_LOCATIONS


def canonical_city(value: object) -> str:
    """Resolve a site-specific location string to one approved city, or empty."""
    text = normalize_city_name(value)
    if text in CANONICAL_CITIES:
        return text

    candidates = {city for city in CANONICAL_CITIES if city in text}
    if not candidates:
        return ""
    if len(candidates) > 1 and re.search(r"[、,，/;；]", text):
        return ""
    # Nested locations such as "嘉兴市桐乡" and "新疆乌鲁木齐" retain the
    # first city-level location rather than becoming a made-up combined name.
    return min(candidates, key=lambda city: (text.index(city), -len(city)))


def city_from_location_text(value: object) -> str:
    candidates: set[str] = set()
    for segment in LOCATION_LABEL_RE.findall(clean_text(value)):
        city = canonical_city(segment)
        if city:
            candidates.add(city)
    return candidates.pop() if len(candidates) == 1 else ""


def resolve_city(city_value: object, district_value: object = "", description: object = "") -> tuple[str, str]:
    """Return a normalized location and whether it is a verifiable city or province-level location."""
    city = canonical_city(city_value)
    if city:
        return city, "city"
    district_city = canonical_city(district_value)
    if district_city:
        return district_city, "city"
    extracted = city_from_location_text(description)
    if extracted:
        return extracted, "city"
    raw_city = normalize_city_name(city_value)
    if raw_city == "全国":
        return raw_city, "province"
    if is_province_level(raw_city) and LOCATION_LABEL_RE.search(clean_text(description)):
        return raw_city, "province"
    return UNKNOWN_CITY, "province" if is_province_level(raw_city) else "unknown"


def parse_zhilian_monthly_salary(value: object) -> tuple[int | None, int | None]:
    """Parse only monthly Zhilian ranges; daily, hourly and per-task pay stay unparsed."""
    text = clean_text(value).replace(" ", "")
    if not text or any(marker in text for marker in ("/天", "/时", "/次")):
        return None, None
    match = ZHILIAN_SALARY_RE.search(text)
    if not match:
        return None, None
    factor = {"万": 10_000, "元": 1, "K": 1_000, "k": 1_000}[match.group("unit")]
    lower = round(float(match.group("lower")) * factor)
    upper = round(float(match.group("upper")) * factor)
    return (lower, upper) if 0 <= lower <= upper else (None, None)

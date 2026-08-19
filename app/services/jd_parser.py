from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class JDRecord:
    id: str
    company: str
    title: str
    location: str
    source_url: str
    collected_at: str
    role_family: str
    content: str
    source_path: str


SKILL_TAXONOMY: dict[str, tuple[str, list[str]]] = {
    "Agent 系统设计": ("Agent", [r"\bAgent\b", r"智能体"]),
    "Python": ("工程", [r"\bPython\b"]),
    "Java/C++/Go": ("工程", [r"\bJava\b", r"C\+\+", r"\bGo\b", r"Rust"]),
    "数据结构与算法": ("工程", [r"数据结构", r"算法基础", r"算法能力"]),
    "Linux/Git": ("工程", [r"\bLinux\b", r"\bGit\b"]),
    "Docker/Kubernetes": ("工程", [r"Docker", r"Kubernetes", r"容器化", r"云原生"]),
    "后端与系统设计": ("工程", [r"后端", r"系统设计", r"高可用", r"分布式系统", r"网络编程"]),
    "LLM/Transformer 原理": ("模型", [r"Transformer", r"大语言模型", r"\bLLM\b", r"大模型.*原理"]),
    "PyTorch/深度学习框架": ("模型", [r"PyTorch", r"TensorFlow", r"深度学习框架"]),
    "微调与后训练": ("模型", [r"SFT", r"LoRA", r"DPO", r"RLHF", r"后训练", r"微调"]),
    "强化学习": ("模型", [r"强化学习", r"\bRL\b", r"PPO", r"GRPO", r"Reward"]),
    "RAG/知识库": ("Agent", [r"\bRAG\b", r"知识库", r"检索增强"]),
    "Agent 框架": ("Agent", [r"LangGraph", r"LangChain", r"AutoGen", r"LlamaIndex", r"CrewAI", r"MetaGPT", r"Dify"]),
    "MCP/工具调用": ("Agent", [r"\bMCP\b", r"Tool Calling", r"Function Calling", r"工具调用", r"Tools?/Skills?"]),
    "规划与推理": ("Agent", [r"Planning", r"Reasoning", r"ReAct", r"Plan-Act", r"多步推理", r"自主规划"]),
    "Memory/上下文工程": ("Agent", [r"Memory", r"记忆系统", r"上下文工程", r"上下文管理", r"上下文压缩"]),
    "Multi-Agent": ("Agent", [r"Multi-Agent", r"多智能体", r"多代理", r"多 Agent"]),
    "Agent 评测": ("评测", [r"评测", r"Evaluation", r"Benchmark", r"成功率", r"失败率"]),
    "数据构建": ("数据", [r"数据构建", r"数据生产", r"数据挖掘", r"合成数据", r"Synthetic Data", r"Trajectory"]),
    "检索与重排序": ("数据", [r"混合检索", r"重排序", r"向量.*检索", r"检索召回"]),
    "Prompt Engineering": ("Agent", [r"Prompt Engineering", r"Prompt工程", r"Prompt 调优"]),
    "推理服务与部署": ("工程", [r"vLLM", r"DeepSpeed", r"TGI", r"推理框架", r"部署", r"服务化", r"性能调优"]),
    "NLP/CV/多模态": ("模型", [r"\bNLP\b", r"\bCV\b", r"多模态", r"视觉理解", r"VLM"]),
    "产品与用户研究": ("产品", [r"产品规划", r"需求分析", r"用户研究", r"交互设计", r"产品文档", r"竞品分析"]),
    "数据分析与指标": ("产品", [r"数据分析", r"业务指标", r"采纳率", r"成本.*指标"]),
}


def _metadata(text: str, label: str) -> str:
    match = re.search(rf"^-[ \t]*{re.escape(label)}[：:][ \t]*([^\r\n]*)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _role_family(title: str, content: str) -> str:
    if "产品" in title:
        return "product"
    if re.search(r"平台|研发工程师|后端", title):
        return "application"
    if re.search(r"预训练|模型训练|后训练", content) and "算法" in title:
        return "algorithm"
    return "application"


def parse_jd_file(path: Path, root: Path) -> JDRecord:
    text = path.read_text(encoding="utf-8")
    title = _metadata(text, "岗位名称") or path.stem
    content_match = re.search(r"##\s*(?:JD 原文|结构化要求)\s*(.*)", text, re.DOTALL)
    content = content_match.group(1).strip() if content_match else text
    return JDRecord(
        id=re.sub(r"\D", "", path.stem) or path.stem,
        company=_metadata(text, "公司") or "未标注",
        title=title,
        location=_metadata(text, "工作地点"),
        source_url=_metadata(text, "原始链接"),
        collected_at=_metadata(text, "收集日期"),
        role_family=_role_family(title, content),
        content=content,
        source_path=str(path.relative_to(root)),
    )


def load_jds(data_dir: Path, role_family: str = "all") -> list[JDRecord]:
    root = data_dir.parent.parent
    paths = [path for path in sorted(data_dir.iterdir()) if path.is_file() and not path.name.startswith(".")]
    records = [parse_jd_file(path, root) for path in paths]
    if role_family != "all":
        records = [record for record in records if record.role_family == role_family]
    return records


def _requirement_type(line: str, preferred_section: bool) -> str:
    if preferred_section or re.search(r"加分|优先", line, re.I):
        return "preferred"
    if re.search(r"职位描述|岗位职责|负责|参与|构建|设计|推动", line):
        return "responsibility"
    return "required"


def build_matrix(records: list[JDRecord]) -> list[dict]:
    found: dict[str, dict[str, dict]] = defaultdict(dict)
    for record in records:
        preferred_section = False
        for raw_line in record.content.splitlines():
            line = raw_line.strip(" \t-*●0123456789、.：:")
            if not line:
                continue
            if re.search(r"加分项", line):
                preferred_section = True
            for skill, (category, patterns) in SKILL_TAXONOMY.items():
                if not any(re.search(pattern, line, re.I) for pattern in patterns):
                    continue
                kind = _requirement_type(line, preferred_section)
                existing = found[skill].get(record.id)
                rank = {"preferred": 1, "responsibility": 2, "required": 3}
                evidence = {
                    "jd_id": record.id,
                    "company": record.company,
                    "title": record.title,
                    "type": kind,
                    "excerpt": line[:140],
                    "source_path": record.source_path,
                    "source_url": record.source_url,
                }
                if not existing or rank[kind] > rank[existing["type"]]:
                    found[skill][record.id] = evidence

    total = len(records) or 1
    matrix = []
    for skill, sources_by_jd in found.items():
        sources = list(sources_by_jd.values())
        counts = {
            kind: sum(1 for source in sources if source["type"] == kind)
            for kind in ("required", "responsibility", "preferred")
        }
        weighted = counts["required"] + 0.8 * counts["responsibility"] + 0.6 * counts["preferred"]
        matrix.append({
            "skill": skill,
            "category": SKILL_TAXONOMY[skill][0],
            "jd_count": len(sources),
            "total_jds": len(records),
            "frequency": round(len(sources) / total, 3),
            "required_count": counts["required"],
            "responsibility_count": counts["responsibility"],
            "preferred_count": counts["preferred"],
            "role_weight": round(weighted / total, 3),
            "sources": sorted(sources, key=lambda item: (item["company"], item["jd_id"])),
        })
    return sorted(matrix, key=lambda item: (-item["role_weight"], -item["jd_count"], item["skill"]))


def dataset_summary(records: list[JDRecord]) -> dict:
    families: dict[str, int] = defaultdict(int)
    for record in records:
        families[record.role_family] += 1
    return {
        "jd_count": len(records),
        "families": dict(families),
        "records": [{key: value for key, value in asdict(record).items() if key != "content"} for record in records],
    }

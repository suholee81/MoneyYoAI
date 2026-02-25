#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 분석 결과 통합 목록 자동 생성기
각 폴더별 분석결과_목록.html 파일들을 찾아서 index.html을 자동으로 생성합니다.
"""

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
import html

def find_analysis_files(root_dir="."):
    """분석결과_목록.html 파일들을 찾습니다."""
    analysis_files = []
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file == "분석결과_목록.html":
                full_path = os.path.join(root, file)
                # 경로를 슬래시로 통일
                relative_path = os.path.relpath(full_path, root_dir).replace('\\', '/')
                folder_path = os.path.dirname(relative_path)
                folder_name = os.path.basename(os.path.dirname(relative_path))
                
                analysis_files.append({
                    'full_path': full_path,
                    'relative_path': relative_path,
                    'folder_path': folder_path,
                    'folder_name': folder_name
                })
    
    # 날짜별로 정렬 (최근 날짜가 상위에 오도록)
    def sort_key(x):
        folder_path = x['folder_path']
        # 날짜 패턴 찾기 (YYYY-MM-DD)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', folder_path)
        if date_match:
            date_str = date_match.group(1)
            # 날짜를 역순으로 정렬 (최신 날짜가 먼저)
            date_key = -int(date_str.replace('-', ''))
            
            # 날짜 다음 숫자 폴더 찾기 (예: 2025-08-07/1 → 1)
            number_match = re.search(r'/(\d+)$', folder_path)
            if number_match:
                number = int(number_match.group(1))
                # 큰 숫자가 위에 오도록 역순 정렬
                return (date_key, -number)
            return (date_key, 0)
        return (0, folder_path)
    
    analysis_files.sort(key=sort_key)
    return analysis_files

def parse_html_file(file_path):
    """HTML 파일을 파싱하여 종목 정보를 추출합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # 테이블에서 종목 정보 추출
        stocks = []
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:]  # 헤더 제외
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    stock_code = cells[0].get_text(strip=True)
                    stock_name = cells[1].get_text(strip=True)
                    opinion = cells[2].get_text(strip=True)
                    
                    # onclick 속성에서 파일명 추출 (goToDetail 함수 호출)
                    onclick = row.get('onclick')
                    detail_link = ""
                    if onclick:
                        # onclick="goToDetail('파일명')" 형태에서 파일명 추출
                        match = re.search(r"goToDetail\('([^']+)'\)", onclick)
                        if match:
                            detail_link = match.group(1)
                    
                    # onclick에서 찾지 못한 경우 href 링크에서 찾기
                    if not detail_link:
                        link = cells[1].find('a')
                        if link and link.get('href'):
                            detail_link = link['href']
                    
                    stocks.append({
                        'code': stock_code,
                        'name': stock_name,
                        'opinion': opinion,
                        'detail_link': detail_link
                    })
        
        return stocks
    except Exception as e:
        print(f"파일 파싱 오류 {file_path}: {e}")
        return []

def generate_index_html(analysis_files):
    """index.html 파일을 생성합니다."""
    
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'>
    <title>AI 분석 결과 통합 목록</title>
    <style>
        body { 
            font-family: 'Pretendard', 'Noto Sans KR', Arial, sans-serif; 
            background: #f4f6fb; 
            margin:0; 
            padding:0;
        }
        .container { 
            max-width: 1200px; 
            margin: 40px auto; 
            background: #fff; 
            border-radius: 18px; 
            box-shadow: 0 4px 24px 0 rgba(30,34,90,0.08); 
            padding: 2.5rem 2rem 2rem 2rem;
        }
        h1 { 
            color: #2b3a55; 
            margin-bottom: 2rem; 
            font-size: 2.5rem; 
            font-weight: 700; 
            letter-spacing: -1px;
            text-align: center;
        }
        .date-section {
            margin-bottom: 3rem;
            border: 1px solid #e3e8f0;
            border-radius: 12px;
            overflow: hidden;
        }
        .date-header {
            background: #f7f9fc;
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #e3e8f0;
        }
        .date-title {
            color: #3a405a;
            font-size: 1.3rem;
            font-weight: 600;
            margin: 0;
        }
        .date-content {
            padding: 1.5rem;
        }
        table { 
            width: 100%; 
            border-collapse: separate; 
            border-spacing: 0; 
            background: #fff; 
            border-radius: 12px; 
            overflow: hidden; 
            box-shadow: 0 1px 4px 0 rgba(30,34,90,0.04);
        }
        th, td { 
            padding: 14px 16px; 
            text-align: left; 
            font-size: 1rem;
        }
        th { 
            background: #f7f9fc; 
            color: #3a405a; 
            font-weight: 600; 
            border-bottom: 1px solid #e3e8f0;
        }
        td { 
            background: #fff; 
            border-bottom: 1px solid #f0f2f7;
        }
        tr:last-child td { 
            border-bottom: none;
        }
        tr.clickable:hover { 
            background: #e6f7ff; 
            cursor: pointer;
        }
        .summary-stats {
            display: flex;
            justify-content: space-around;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }
        .stat-card {
            background: #fff;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
            min-width: 150px;
            margin: 0.5rem;
        }
        .stat-number {
            font-size: 2rem;
            font-weight: 700;
            color: #2b3a55;
        }
        .stat-label {
            color: #6b7280;
            margin-top: 0.5rem;
        }
        .folder-link {
            display: inline-block;
            background: #3b82f6;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            text-decoration: none;
            margin: 0.5rem;
            font-weight: 500;
            transition: background-color 0.2s;
        }
        .folder-link:hover {
            background: #2563eb;
        }
        @media (max-width: 600px) {
            .container { 
                padding: 1rem 0.5rem;
                margin: 20px auto;
            }
            h1 { 
                font-size: 1.8rem;
            }
            .date-title {
                font-size: 1.1rem;
            }
            th, td { 
                font-size: 0.95rem; 
                padding: 10px 8px;
            }
            .summary-stats {
                flex-direction: column;
                align-items: center;
            }
        }
    </style>
    <script>
        function goToDetail(filename) {
            window.open(filename, '_blank');
        }
        
        function goToFolder(folderPath) {
            window.location.href = folderPath + '/분석결과_목록.html';
        }
        
        function filterByDate(date) {
            const sections = document.querySelectorAll('.date-section');
            sections.forEach(section => {
                if (date === 'all' || section.dataset.date === date) {
                    section.style.display = 'block';
                } else {
                    section.style.display = 'none';
                }
            });
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>📊 AI 분석 결과 통합 목록</h1>
        
        <div class="summary-stats">
            <div class="stat-card">
                <div class="stat-number" id="totalStocks">0</div>
                <div class="stat-label">총 분석 종목</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="buyCount">0</div>
                <div class="stat-label">매수 고려</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="neutralCount">0</div>
                <div class="stat-label">관망</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="sellCount">0</div>
                <div class="stat-label">매수 부적합</div>
            </div>
        </div>

        <div style="text-align: center; margin-bottom: 2rem;">
            <h3>📁 폴더별 분석 결과 바로가기</h3>
            <div id="folder-links">
                <!-- 폴더 링크들이 여기에 동적으로 추가됩니다 -->
            </div>
        </div>
'''
    
    # 폴더별로 그룹화
    folder_groups = {}
    for file_info in analysis_files:
        folder_path = file_info['folder_path']
        if folder_path not in folder_groups:
            folder_groups[folder_path] = []
        folder_groups[folder_path].append(file_info)
    
    # 각 폴더별로 섹션 생성
    for folder_path, files in folder_groups.items():
        # 폴더명에서 날짜 추출
        folder_name = os.path.basename(folder_path)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', folder_name)
        if date_match:
            date_str = date_match.group(1)
            display_date = f"{date_str[:4]}년 {date_str[5:7]}월 {date_str[8:10]}일"
        else:
            display_date = folder_name
        
        # 전체 폴더 경로를 표시 (날짜폴더 포함)
        full_folder_display = folder_path.replace('\\', '/')  # Windows 경로 구분자 통일
        folder_path_slash = folder_path.replace('\\', '/')
        
        html_content += f'''
        <!-- {folder_path} -->
        <div class="date-section" data-date="{folder_path}">
            <div class="date-header">
                <h2 class="date-title">📅 {full_folder_display} 분석 결과</h2>
                <a href="{folder_path_slash}/분석결과_목록.html" class="folder-link" target="_blank">
                    📁 폴더 열기
                </a>
            </div>
            <div class="date-content">
                <table>
                    <thead>
                        <tr>
                            <th>종목코드</th>
                            <th>종목명</th>
                            <th>최종 투자의견</th>
                        </tr>
                    </thead>
                    <tbody>
'''
        
        # 각 파일의 종목 정보 추가
        for file_info in files:
            stocks = parse_html_file(file_info['full_path'])
            for stock in stocks:
                # 상세 페이지 링크 생성
                if stock['detail_link']:
                    if stock['detail_link'].startswith('http'):
                        detail_path = stock['detail_link']
                    else:
                        # 상대 경로인 경우 폴더 경로와 결합
                        # Windows 경로 구분자를 슬래시로 통일
                        folder_path_slash = folder_path.replace('\\', '/')
                        detail_path = f"{folder_path_slash}/{stock['detail_link']}"
                else:
                    # detail_link가 없는 경우 기본 파일명으로 생성
                    folder_path_slash = folder_path.replace('\\', '/')
                    detail_path = f"{folder_path_slash}/{stock['code']}_{stock['name']}.html"
                
                # 투자의견에 따른 이모지 추가
                opinion = stock['opinion']
                emoji = "📊"
                if any(word in opinion for word in ['매수', 'Buy', 'BUY', '적극', 'Strong']):
                    emoji = "✅"
                elif any(word in opinion for word in ['관망', 'Neutral', 'Wait', '중립']):
                    emoji = "🟡"
                elif any(word in opinion for word in ['매도', 'Sell', '부적합', 'Avoid', '보류']):
                    emoji = "🔴"
                
                html_content += f'''
                        <tr class="clickable" onclick="goToDetail('{detail_path}')">
                            <td>{stock['code']}</td>
                            <td><a href="{detail_path}" style="color:inherit;text-decoration:none;" target="_blank">{stock['name']}</a></td>
                            <td>{emoji} {html.escape(opinion)}</td>
                        </tr>
'''
        
        html_content += '''
                    </tbody>
                </table>
            </div>
        </div>
'''
    
    # 폴더 링크들을 위한 JavaScript 추가
    html_content += '''
        </div>

        <script>
            // 폴더 링크 생성
            function generateFolderLinks() {
                const folderLinks = document.getElementById('folder-links');
                const sections = document.querySelectorAll('.date-section');
                
                sections.forEach(section => {
                    const date = section.dataset.date;
                    const title = section.querySelector('.date-title').textContent;
                    const link = document.createElement('a');
                    link.href = date + '/분석결과_목록.html';
                    link.className = 'folder-link';
                    // 날짜폴더까지 포함된 전체 경로 표시
                    link.textContent = title.replace('📅 ', '');
                    link.target = '_blank';
                    folderLinks.appendChild(link);
                });
            }
            
            // 통계 계산
            function calculateStats() {
                const rows = document.querySelectorAll('tbody tr');
                let buyCount = 0;
                let neutralCount = 0;
                let sellCount = 0;
                
                rows.forEach(row => {
                    const opinion = row.querySelector('td:last-child').textContent;
                    if (opinion.includes('매수') || opinion.includes('Buy') || opinion.includes('BUY') || opinion.includes('적극') || opinion.includes('Strong')) {
                        buyCount++;
                    } else if (opinion.includes('관망') || opinion.includes('Neutral') || opinion.includes('Wait') || opinion.includes('중립')) {
                        neutralCount++;
                    } else if (opinion.includes('매도') || opinion.includes('Sell') || opinion.includes('부적합') || opinion.includes('Avoid') || opinion.includes('보류')) {
                        sellCount++;
                    }
                });
                
                const totalStocks = buyCount + neutralCount + sellCount;
                
                document.getElementById('totalStocks').textContent = totalStocks;
                document.getElementById('buyCount').textContent = buyCount;
                document.getElementById('neutralCount').textContent = neutralCount;
                document.getElementById('sellCount').textContent = sellCount;
            }
            
            // 페이지 로드 시 실행
            window.addEventListener('load', function() {
                generateFolderLinks();
                calculateStats();
            });
        </script>
    </body>
</html>'''
    
    return html_content

def main():
    """메인 함수"""
    # 스크립트가 있는 디렉토리로 이동
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("🔍 AI 분석 결과 파일들을 찾는 중...")
    
    # 분석 파일들 찾기
    analysis_files = find_analysis_files()
    
    if not analysis_files:
        print("❌ 분석결과_목록.html 파일을 찾을 수 없습니다.")
        return
    
    print(f"✅ {len(analysis_files)}개의 분석 파일을 찾았습니다:")
    for file_info in analysis_files:
        print(f"   - {file_info['relative_path']}")
    
    # index.html 생성
    print("\n📝 index.html 파일을 생성하는 중...")
    html_content = generate_index_html(analysis_files)
    
    # 파일 저장
    output_file = "index.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ {output_file} 파일이 성공적으로 생성되었습니다!")
    print(f"📊 총 {len(analysis_files)}개 폴더의 분석 결과가 통합되었습니다.")
    
    # 통계 정보 출력
    total_stocks = 0
    for file_info in analysis_files:
        stocks = parse_html_file(file_info['full_path'])
        total_stocks += len(stocks)
    
    print(f"📈 총 {total_stocks}개 종목의 분석 결과가 포함되었습니다.")

if __name__ == "__main__":
    main() 
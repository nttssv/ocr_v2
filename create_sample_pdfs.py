#!/usr/bin/env python3
"""
Script to create sample PDF files for testing the OCR API.
This creates simple PDF files with text content for testing purposes.
"""

import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch

def create_sample_pdf(filename, content, page_size=A4):
    """Create a PDF file with the given content."""
    c = canvas.Canvas(filename, pagesize=page_size)
    width, height = page_size
    
    # Set up text
    c.setFont("Helvetica", 12)
    
    # Split content into lines and write to PDF
    lines = content.split('\n')
    y_position = height - 50  # Start from top
    
    for line in lines:
        if y_position < 50:  # Start new page if needed
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = height - 50
        
        c.drawString(50, y_position, line)
        y_position -= 20
    
    c.save()
    print(f"Created {filename}")

def main():
    # Create samples directory if it doesn't exist
    samples_dir = "samples"
    os.makedirs(samples_dir, exist_ok=True)
    
    # Sample 1: Vietnamese legal document
    vietnamese_content = """CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc

QUYẾT ĐỊNH
Số: 123/2024/QĐ-UBND

Về việc phê duyệt dự án đầu tư

UỶ BAN NHÂN DÂN TỈNH ABC

Căn cứ Luật Tổ chức chính quyền địa phương năm 2015;
Căn cứ Luật Đầu tư năm 2020;
Căn cứ Nghị định số 31/2021/NĐ-CP ngày 26/3/2021;
Xét đề nghị của Sở Kế hoạch và Đầu tư tỉnh ABC;

QUYẾT ĐỊNH:

Điều 1. Phê duyệt dự án đầu tư:
- Tên dự án: Dự án xây dựng nhà máy sản xuất
- Địa điểm: Khu công nghiệp XYZ, tỉnh ABC
- Quy mô đầu tư: 100 tỷ đồng
- Thời gian thực hiện: 24 tháng

Điều 2. Quyết định này có hiệu lực kể từ ngày ký.

Điều 3. Các ông/bà Giám đốc các Sở, ban, ngành;
Chủ tịch UBND các huyện, thành phố thuộc tỉnh;
Các tổ chức, cá nhân có liên quan chịu trách nhiệm
thi hành Quyết định này.

Nơi nhận:
- Như Điều 3;
- Lưu: VT, KHĐT.

TM. UỶ BAN NHÂN DÂN TỈNH
CHỦ TỊCH

Nguyễn Văn A"""
    
    # Sample 2: English business document
    english_content = """BUSINESS PROPOSAL

Project: Digital Transformation Initiative
Date: January 15, 2024
Prepared by: Technology Solutions Inc.

EXECUTIVE SUMMARY

This proposal outlines a comprehensive digital transformation
strategy for modernizing business operations and improving
efficiency through technology adoption.

OBJECTIVES:
1. Streamline business processes
2. Improve customer experience
3. Reduce operational costs
4. Enhance data analytics capabilities

PROPOSED SOLUTION:

Phase 1: Infrastructure Assessment (2 months)
- Current system evaluation
- Gap analysis
- Technology roadmap development

Phase 2: Implementation (6 months)
- Cloud migration
- Process automation
- Staff training

Phase 3: Optimization (3 months)
- Performance monitoring
- Continuous improvement
- ROI measurement

BUDGET ESTIMATE:
Total Project Cost: $250,000
- Phase 1: $50,000
- Phase 2: $150,000
- Phase 3: $50,000

TIMELINE:
Project Duration: 11 months
Start Date: February 1, 2024
Completion Date: December 31, 2024

CONTACT INFORMATION:
John Smith, Project Manager
Email: john.smith@techsolutions.com
Phone: (555) 123-4567"""
    
    # Sample 3: Mixed content document
    mixed_content = """TECHNICAL SPECIFICATION
Dự án Phát triển Phần mềm / Software Development Project

Project Overview:
This document contains both English and Vietnamese content
to test multi-language OCR capabilities.

Thông tin dự án:
- Tên dự án: Hệ thống quản lý tài liệu
- Project Name: Document Management System
- Ngôn ngữ lập trình: Python, JavaScript
- Programming Languages: Python, JavaScript

Technical Requirements:
1. Database: PostgreSQL
2. Backend: FastAPI
3. Frontend: React.js
4. Authentication: OAuth 2.0

Yêu cầu kỹ thuật:
1. Cơ sở dữ liệu: PostgreSQL
2. Backend: FastAPI
3. Frontend: React.js
4. Xác thực: OAuth 2.0

Features / Tính năng:
- Document upload and storage
- Tải lên và lưu trữ tài liệu
- OCR text extraction
- Trích xuất văn bản OCR
- Search and indexing
- Tìm kiếm và đánh chỉ mục

Deployment / Triển khai:
- Docker containers
- Kubernetes orchestration
- CI/CD pipeline with GitHub Actions

Contact / Liên hệ:
Developer: Nguyễn Văn B
Email: developer@company.com
Phone: +84 123 456 789"""
    
    # Sample 4: Table-like content
    table_content = """FINANCIAL REPORT - BÁO CÁO TÀI CHÍNH
Quarter 4, 2023 - Quý 4, 2023

REVENUE BREAKDOWN / PHÂN TÍCH DOANH THU:

Product Category    Q3 2023    Q4 2023    Growth
Sản phẩm A         $125,000   $145,000   +16%
Sản phẩm B         $89,000    $92,000    +3.4%
Sản phẩm C         $67,000    $78,000    +16.4%
Dịch vụ tư vấn     $45,000    $52,000    +15.6%

TOTAL REVENUE      $326,000   $367,000   +12.6%
TỔNG DOANH THU

EXPENSES / CHI PHÍ:
Operating Costs    $180,000   $195,000
Chi phí hoạt động

Marketing          $25,000    $28,000
Tiếp thị

R&D                $35,000    $40,000
Nghiên cứu phát triển

TOTAL EXPENSES     $240,000   $263,000
TỔNG CHI PHÍ

NET PROFIT         $86,000    $104,000   +20.9%
LỢI NHUẬN RÒNG

KEY METRICS / CHỈ SỐ QUAN TRỌNG:
- Profit Margin: 28.3%
- Tỷ suất lợi nhuận: 28.3%
- Customer Growth: 15%
- Tăng trưởng khách hàng: 15%
- Employee Count: 45
- Số lượng nhân viên: 45

PREPARED BY / NGƯỜI LẬP:
Finance Department
Phòng Tài chính
Date: January 10, 2024"""
    
    # Create the PDF files
    create_sample_pdf(os.path.join(samples_dir, "1.pdf"), vietnamese_content)
    create_sample_pdf(os.path.join(samples_dir, "2.pdf"), english_content)
    create_sample_pdf(os.path.join(samples_dir, "3.pdf"), mixed_content)
    create_sample_pdf(os.path.join(samples_dir, "4.pdf"), table_content)
    
    print(f"\nCreated 4 sample PDF files in {samples_dir}/ directory")
    print("Files created:")
    for i in range(1, 5):
        filepath = os.path.join(samples_dir, f"{i}.pdf")
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"  {i}.pdf ({size:,} bytes)")

if __name__ == "__main__":
    main()
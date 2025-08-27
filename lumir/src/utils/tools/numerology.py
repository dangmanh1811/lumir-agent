
from datetime import datetime
from typing import Dict, List, Set, Tuple, Union
import pytz
from dotenv import load_dotenv
import os
import boto3
from botocore.client import Config
from docx import Document
from io import BytesIO

load_dotenv()

class S3Client:
    
    def __init__(self):
        self.s3 = boto3.client('s3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION'),
            endpoint_url=os.getenv('AWS_ENDPOINT_URL'),
            config=Config(s3={"addressing_style": "virtual"})
        )
        self.bucket_name = os.getenv('BUCKET_NAME')

    def get_document_text_for_numerology(self, number_type: str, number: int, milestone_number: int = None, challenge_number: int = None) -> str:
        """

        Args:
            number_type (str): Loại số, ví dụ 'life_path', 'personal_day', 'personal_year', etc.
            number (int): Giá trị số.
            milestone_number (int): Số thứ tự milestone (1-4)
            challenge_number (int): Số thứ tự challenge (1-4)

        Returns:
            str: Nội dung văn bản của tài liệu.
        """
        # Map number types to folder and file naming conventions
        base_folder = "numerology_trader"
        
        if number_type == "personal_year":
            folder = f"{base_folder}/nam_ca_nhan"
            file_name = f"nam_ca_nhan_{number}.docx"
        elif number_type == "personal_day":
            folder = f"{base_folder}/ngay_ca_nhan"
            file_name = f"ngay_ca_nhan_{number}.docx"
        elif number_type == "personal_month":
            folder = f"{base_folder}/thang_ca_nhan"
            file_name = f"thang_ca_nhan_{number}.docx"
        elif number_type == "life_path":
            folder = f"{base_folder}/duong_doi"
            file_name = f"duong_doi_{number}.docx"
        elif number_type == "life_purpose":
            folder = f"{base_folder}/su_menh"
            file_name = f"su_menh_{number}.docx"
        elif number_type == "soul":
            folder = f"{base_folder}/linh_hon"
            file_name = f"linh_hon_{number}.docx"
        elif number_type == "personality":
            folder = f"{base_folder}/nhan_cach"
            file_name = f"nhan_cach_{number}.docx"
        elif number_type == "balance":
            folder = f"{base_folder}/can_bang"
            file_name = f"can_bang_{number}.docx"
        elif number_type == "maturity":
            folder = f"{base_folder}/truong_thanh"
            file_name = f"truong_thanh_{number}.docx"
        elif number_type == "passion":
            folder = f"{base_folder}/dam_me"
            file_name = f"dam_me_{number}.docx"
        elif number_type == "missing_aspects":
            folder = f"{base_folder}/thieu"
            file_name = f"thieu_{number}.docx"
        elif number_type == "rational_thinking":
            folder = f"{base_folder}/tu_duy_ly_tri"
            file_name = f"tu_duy_ly_tri_{number}.docx"
        elif number_type in ("milestone", "giai_doan"):
            folder = f"{base_folder}/giai_doan_{milestone_number}"
            file_name = f"chang_{number}.docx"
        elif number_type in ("challenge", "thu_thach"):
            folder = f"{base_folder}/thach_thuc_giai_doan_{challenge_number}"
            file_name = f"thach_thuc_{number}.docx"
        else:
            return f"Tài liệu cho {number_type} với giá trị {number} chưa có sẵn."

        file_key = f"{folder}/{file_name}"
        print(f"[S3 Numerology] Fetching: bucket={self.bucket_name}, key={file_key}")

        if self.s3 is None:
            raise ValueError("S3 client không được khởi tạo.")

        try:
            # Check if bucket exists and is accessible
            try:
                self.s3.head_bucket(Bucket=self.bucket_name)
                print(f"✅ Bucket {self.bucket_name} is accessible")
            except Exception as bucket_error:
                print(f"⚠️ Bucket access issue: {bucket_error}")
                return f"Không thể truy cập bucket {self.bucket_name}: {bucket_error}"
            
            # Try to get the object
            try:
                obj = self.s3.get_object(Bucket=self.bucket_name, Key=file_key)
                
                # Check if Body exists and is readable
                if "Body" not in obj:
                    print(f"⚠️ No Body in S3 response: {obj.keys()}")
                    return f"Response không có Body: {list(obj.keys())}"
                
                body = obj["Body"]
                if body is None:
                    print(f"⚠️ Body is None")
                    return f"Body của response là None"
                
                # Read the content
                try:
                    file_content = body.read()
                except Exception as read_error:
                    print(f"⚠️ Error reading body: {read_error}")
                    return f"Lỗi đọc body: {read_error}"
                
                # Check if content is valid
                if not file_content:
                    print(f"⚠️ File content is empty")
                    return f"File content rỗng"
                
                # Try to parse as document
                try:
                    doc = Document(BytesIO(file_content))
                    
                    # Extract text
                    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
                    if not paragraphs:
                        print(f"⚠️ No text content in document")
                        return f"Document không có nội dung text"
                    
                    text = "\n".join(paragraphs)
                    return text
                    
                except Exception as doc_error:
                    print(f"⚠️ Error parsing document: {doc_error}")
                    return f"Lỗi parse document: {doc_error}"
                    
            except Exception as obj_error:
                print(f"⚠️ Error getting object: {obj_error}")
                return f"Lỗi lấy object: {obj_error}"
                
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return f"Lỗi không mong đợi: {str(e)}"


class CalNum:
    """
    Personal Numerology Calculator implementing Vietnamese numerology principles.

    Supports calculation of life path, soul number, personality number,
    and other key numerological indicators.
    """

    # Vietnamese alphabet mapping (A=1, B=2, ..., I=9, J=1, ...)
    ALPHABET = {
        # Basic letters
        'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9,
        'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'O': 6, 'P': 7, 'Q': 8, 'R': 9,
        'S': 1, 'T': 2, 'U': 3, 'V': 4, 'W': 5, 'X': 6, 'Y': 7, 'Z': 8,

        # Vietnamese vowels with diacritics
        'Ă': 1, 'Â': 1, 'Ê': 5, 'Ô': 6, 'Ơ': 6,

        # Vietnamese consonants with diacritics
        'Đ': 4,

        # Vowels with tone marks
        'Á': 1, 'À': 1, 'Ả': 1, 'Ã': 1, 'Ạ': 1,
        'Ắ': 1, 'Ằ': 1, 'Ẳ': 1, 'Ẵ': 1, 'Ặ': 1,
        'Ấ': 1, 'Ầ': 1, 'Ẩ': 1, 'Ẫ': 1, 'Ậ': 1,
        'É': 5, 'È': 5, 'Ẻ': 5, 'Ẽ': 5, 'Ẹ': 5,
        'Ế': 5, 'Ề': 5, 'Ể': 5, 'Ễ': 5, 'Ệ': 5,
        'Í': 9, 'Ì': 9, 'Ỉ': 9, 'Ĩ': 9, 'Ị': 9,
        'Ó': 6, 'Ò': 6, 'Ỏ': 6, 'Õ': 6, 'Ọ': 6,
        'Ố': 6, 'Ồ': 6, 'Ổ': 6, 'Ỗ': 6, 'Ộ': 6,
        'Ớ': 6, 'Ờ': 6, 'Ở': 6, 'Ỡ': 6, 'Ợ': 6,

        # U vowels with tone marks
        'Ú': 3, 'Ù': 3, 'Ủ': 3, 'Ũ': 3, 'Ụ': 3,
        'Ư': 3, 'Ứ': 3, 'Ừ': 3, 'Ử': 3, 'Ữ': 3, 'Ự': 3,

        # Y vowels with tone marks
        'Ý': 7, 'Ỳ': 7, 'Ỷ': 7, 'Ỹ': 7, 'Ỵ': 7
    }

    # Master numbers that should not be reduced
    MASTER_NUMBERS = {11, 22, 33}

    # Karmic debt numbers
    KARMIC_NUMBERS = {13, 14, 16, 19}

    def __init__(self, dob: str, name: str, current_date: str = None):
        """
        Khởi tạo calculator với thông tin cá nhân.
        
        Args:
            dob (str): Ngày sinh theo định dạng dd/mm/yyyy
            name (str): Họ và tên đầy đủ
            current_date (str): Ngày hiện tại (optional)
        """
        self.name = name.strip()
        self.dob_date = self._parse_date(dob, "birth")
        
        # Extract day, month, year from birth date
        self.day = self.dob_date.day
        self.month = self.dob_date.month
        self.year = self.dob_date.year
        
        # Set current date
        if current_date:
            self.current_datetime = self._parse_date(current_date, "current")
        else:
            # Use Vietnam timezone
            vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            self.current_datetime = datetime.now(vietnam_tz)
        
        # Convert name to numbers for calculations
        self.name_numbers = self._name_to_numbers()

    def _parse_date(self, date_str: str, date_type: str) -> datetime:
        """
        Parse date string to datetime object.
        
        Args:
            date_str (str): Date string in dd/mm/yyyy format
            date_type (str): Type of date for error messages
            
        Returns:
            datetime: Parsed datetime object
        """
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            raise ValueError(f"Invalid {date_type} date format. Use dd/mm/yyyy")

    def _name_to_numbers(self) -> List[int]:
        """
        Convert name characters to their corresponding numbers.
        
        Returns:
            List[int]: List of numbers corresponding to each character
        """
        return [self.ALPHABET.get(char.upper(), 0) for char in self.name if char.upper() in self.ALPHABET]

    def reduce_number(self, n: int) -> int:
        """
        Reduce number to single digit, preserving master numbers 11, 22, 33.
        
        Args:
            n (int): Number to reduce
            
        Returns:
            int: Reduced number
        """
        while n > 9:
            if n in self.MASTER_NUMBERS:
                return n
            n = sum(int(digit) for digit in str(n))
        return n

    def reduce_number_no_master(self, n: int) -> int:
        """
        Reduce number to single digit without preserving master numbers.
        
        Args:
            n (int): Number to reduce
            
        Returns:
            int: Reduced number (1-9)
        """
        while n > 9:
            n = sum(int(digit) for digit in str(n))
        return n

    def reduce_number_with_masters(self, n: int, masters: Set[int] = None) -> int:
        """
        Reduce number with specific master numbers to preserve.
        
        Args:
            n (int): Number to reduce
            masters (Set[int]): Set of master numbers to preserve
            
        Returns:
            int: Reduced number
        """
        if masters is None:
            masters = self.MASTER_NUMBERS
            
        while n > 9:
            if n in masters:
                return n
            n = sum(int(digit) for digit in str(n))
        return n

    def reduce_to_single_digit(self, n: int) -> int:
        """
        Force reduction to single digit (1-9).
        
        Args:
            n (int): Number to reduce
            
        Returns:
            int: Single digit (1-9)
        """
        while n > 9:
            n = sum(int(digit) for digit in str(n))
        return n

    def _is_vowel(self, char: str, current_word: str = None) -> bool:
        """
        Check if character is a vowel in Vietnamese.
        
        Args:
            char (str): Character to check
            current_word (str): Current word context
            
        Returns:
            bool: True if character is vowel
        """
        vowels = {
            'A', 'E', 'I', 'O', 'U', 'Y',
            'Ă', 'Â', 'Ê', 'Ô', 'Ơ', 'Ư',
            'Á', 'À', 'Ả', 'Ã', 'Ạ',
            'Ắ', 'Ằ', 'Ẳ', 'Ẵ', 'Ặ',
            'Ấ', 'Ầ', 'Ẩ', 'Ẫ', 'Ậ',
            'É', 'È', 'Ẻ', 'Ẽ', 'Ẹ',
            'Ế', 'Ề', 'Ể', 'Ễ', 'Ệ',
            'Í', 'Ì', 'Ỉ', 'Ĩ', 'Ị',
            'Ó', 'Ò', 'Ỏ', 'Õ', 'Ọ',
            'Ố', 'Ồ', 'Ổ', 'Ỗ', 'Ộ',
            'Ớ', 'Ờ', 'Ở', 'Ỡ', 'Ợ',
            'Ú', 'Ù', 'Ủ', 'Ũ', 'Ụ',
            'Ứ', 'Ừ', 'Ử', 'Ữ', 'Ự',
            'Ý', 'Ỳ', 'Ỷ', 'Ỹ', 'Ỵ'
        }
        
        char_upper = char.upper()
        
        # Special handling for Y
        if char_upper == 'Y':
            if current_word:
                return self._is_y_vowel_in_word(char, current_word)
            else:
                # Find the word containing this Y
                word = self._find_word_with_char_at_position(char)
                return self._is_y_vowel_in_word(char, word) if word else True
        
        return char_upper in vowels

    def _is_y_vowel_in_word(self, char: str, word: str) -> bool:
        """
        Determine if Y is a vowel in the given word context.
        
        Args:
            char (str): The Y character
            word (str): The word containing Y
            
        Returns:
            bool: True if Y acts as vowel in this word
        """
        word_upper = word.upper()
        
        # Y is consonant in these cases
        consonant_patterns = [
            'YÊU', 'YẾU', 'YỀU', 'YỂU', 'YỄU', 'YỆU',
            'YÊN', 'YẾN', 'YỀN', 'YỂN', 'YỄN', 'YỆN'
        ]
        
        for pattern in consonant_patterns:
            if pattern in word_upper:
                return False
        
        # Y is vowel in most other cases
        return True

    def _find_word_with_char_at_position(self, char: str) -> str:
        """
        Find the word containing the character at its position in the name.
        
        Args:
            char (str): Character to find
            
        Returns:
            str: Word containing the character
        """
        words = self.name.split()
        char_position = 0
        
        for word in words:
            for word_char in word:
                if word_char == char and char_position == len([c for c in self.name[:self.name.index(char)] if c.isalpha()]):
                    return word
                if word_char.isalpha():
                    char_position += 1
        
        return ""

    def _is_consonant(self, char: str, current_word: str = None) -> bool:
        """
        Check if character is a consonant.
        
        Args:
            char (str): Character to check
            current_word (str): Current word context
            
        Returns:
            bool: True if character is consonant
        """
        return not self._is_vowel(char, current_word) and char.upper() in self.ALPHABET

    def _split_name_parts(self) -> List[str]:
        """
        Split name into parts (words).
        
        Returns:
            List[str]: List of name parts
        """
        return [part.strip() for part in self.name.split() if part.strip()]

    def calculate_life_path(self) -> int:
        """
        Calculate Life Path number.
        
        Formula: reduce(day + month + year) with master numbers
        
        Returns:
            int: Life Path number
        """
        total = self.day + self.month + self.year
        return self.reduce_number(total)

    def calculate_life_purpose(self) -> int:
        """
        Calculate Life Purpose number.
        
        Formula: reduce(sum of all letters in full name) with master numbers
        
        Returns:
            int: Life Purpose number
        """
        total = sum(self.name_numbers)
        return self.reduce_number(total)

    def calculate_balance(self) -> int:
        """
        Calculate Balance number.
        
        Formula: reduce(sum of first letters of each name part) no master
        
        Returns:
            int: Balance number
        """
        name_parts = self._split_name_parts()
        if not name_parts:
            return 0
            
        first_letters_sum = sum(
            self.ALPHABET.get(part[0].upper(), 0)
            for part in name_parts
            if part and part[0].upper() in self.ALPHABET
        )
        
        return self.reduce_number_no_master(first_letters_sum)

    def calculate_soul(self) -> int:
        """
        Calculate Soul number.
        
        Formula: reduce(sum of vowels in full name) with master numbers
        
        Returns:
            int: Soul number
        """
        vowel_sum = 0
        words = self._split_name_parts()
        
        for word in words:
            for char in word:
                if self._is_vowel(char, word):
                    vowel_sum += self.ALPHABET.get(char.upper(), 0)
        
        return self.reduce_number(vowel_sum)

    def calculate_personality(self) -> int:
        """
        Calculate Personality number.
        
        Formula: reduce(sum of consonants in full name) with master numbers
        
        Returns:
            int: Personality number
        """
        consonant_sum = 0
        words = self._split_name_parts()
        
        for word in words:
            for char in word:
                if self._is_consonant(char, word):
                    consonant_sum += self.ALPHABET.get(char.upper(), 0)
        
        return self.reduce_number(consonant_sum)

    def calculate_birth_day(self) -> int:
        """
        Calculate Birth Day number.
        
        Formula: reduce(day) no master
        
        Returns:
            int: Birth Day number
        """
        return self.reduce_number_no_master(self.day)

    def calculate_subconscious_strength(self) -> int:
        """
        Calculate Subconscious Strength.
        
        Formula: Count unique numbers (1-9) present in full name
        
        Returns:
            int: Subconscious Strength (1-9)
        """
        unique_numbers = set()
        for num in self.name_numbers:
            if 1 <= num <= 9:
                unique_numbers.add(num)
        return len(unique_numbers)

    def calculate_maturity(self) -> int:
        """
        Calculate Maturity number.
        
        Formula: reduce(life_path + life_purpose) with master numbers
        
        Returns:
            int: Maturity number
        """
        life_path = self.calculate_life_path()
        life_purpose = self.calculate_life_purpose()
        return self.reduce_number(life_path + life_purpose)

    def get_missing_aspects(self) -> Set[int]:
        """
        Get missing numbers (1-9) in the name.
        
        Returns:
            Set[int]: Set of missing numbers
        """
        present_numbers = set()
        for num in self.name_numbers:
            if 1 <= num <= 9:
                present_numbers.add(num)
        
        all_numbers = set(range(1, 10))
        return all_numbers - present_numbers

    def check_karmic_debt(self) -> str:
        """
        Check for karmic debt numbers in the calculation process.
        
        Returns:
            str: Karmic debt information
        """
        karmic_debts = []
        
        # Check life path calculation
        life_path_sum = self.day + self.month + self.year
        if life_path_sum in self.KARMIC_NUMBERS:
            karmic_debts.append(f"Life Path: {life_path_sum}")
        
        # Check life purpose calculation
        life_purpose_sum = sum(self.name_numbers)
        if life_purpose_sum in self.KARMIC_NUMBERS:
            karmic_debts.append(f"Life Purpose: {life_purpose_sum}")
        
        if karmic_debts:
            return ", ".join(karmic_debts)
        return "No karmic debt detected"

    def calculate_passion(self) -> List[int]:
        """
        Calculate Passion numbers (most frequent numbers in name).
        
        Returns:
            List[int]: List of passion numbers
        """
        from collections import Counter
        
        # Count frequency of each number (1-9) in name
        number_counts = Counter()
        for num in self.name_numbers:
            if 1 <= num <= 9:
                number_counts[num] += 1
        
        if not number_counts:
            return []
        
        # Find maximum frequency
        max_count = max(number_counts.values())
        
        # Return all numbers with maximum frequency
        passion_numbers = [num for num, count in number_counts.items() if count == max_count]
        return sorted(passion_numbers)

    def get_societal_adaptability_index(self) -> str:
        """
        Get Societal Adaptability Index based on name structure.
        
        Returns:
            str: Adaptability index description
        """
        name_parts = self._split_name_parts()
        num_parts = len(name_parts)
        
        if num_parts <= 2:
            return "High adaptability - Simple name structure"
        elif num_parts == 3:
            return "Moderate adaptability - Balanced name structure"
        else:
            return "Lower adaptability - Complex name structure"

    def calculate_emotional_response_style(self) -> int:
        """
        Calculate Emotional Response Style.
        
        Formula: reduce(sum of vowels in first name) no master
        
        Returns:
            int: Emotional Response Style number
        """
        name_parts = self._split_name_parts()
        if not name_parts:
            return 0
        
        first_name = name_parts[0]
        vowel_sum = 0
        
        for char in first_name:
            if self._is_vowel(char, first_name):
                vowel_sum += self.ALPHABET.get(char.upper(), 0)
        
        return self.reduce_number_no_master(vowel_sum)

    def calculate_link_connection(self) -> int:
        """
        Calculate Life Path - Life Purpose Link.
        
        Formula: reduce(life_path + life_purpose) no master
        
        Returns:
            int: Link connection number
        """
        life_path = self.calculate_life_path()
        life_purpose = self.calculate_life_purpose()
        return self.reduce_number_no_master(life_path + life_purpose)

    def calculate_soul_personality_link(self) -> int:
        """
        Calculate Soul - Personality Link.
        
        Formula: reduce(soul + personality) no master
        
        Returns:
            int: Soul-Personality link number
        """
        soul = self.calculate_soul()
        personality = self.calculate_personality()
        return self.reduce_number_no_master(soul + personality)

    def calculate_milestone_phase(self) -> Dict[str, int]:
        """
        Calculate Milestone Phase numbers.
        
        Returns:
            Dict[str, int]: Dictionary with milestone phases
        """
        milestone_1 = self.reduce_number_no_master(self.month)
        milestone_2 = self.reduce_number_no_master(self.day)
        milestone_3 = self.reduce_number_no_master(self.year)
        milestone_4 = self.reduce_number_no_master(milestone_1 + milestone_2 + milestone_3)
        
        return {
            "milestone_1": milestone_1,
            "milestone_2": milestone_2,
            "milestone_3": milestone_3,
            "milestone_4": milestone_4
        }

    def calculate_challenge(self) -> Dict[str, int]:
        """
        Calculate Challenge numbers.
        
        Returns:
            Dict[str, int]: Dictionary with challenge numbers
        """
        milestone = self.calculate_milestone_phase()
        
        challenge_1 = abs(milestone["milestone_1"] - milestone["milestone_2"])
        challenge_2 = abs(milestone["milestone_3"] - milestone["milestone_1"])
        challenge_3 = abs(challenge_1 - challenge_2)
        challenge_4 = abs(milestone["milestone_2"] - milestone["milestone_3"])
        
        return {
            "challenge_1": challenge_1,
            "challenge_2": challenge_2,
            "challenge_3": challenge_3,
            "challenge_4": challenge_4
        }

    def calculate_rational_thinking(self) -> int:
        """
        Calculate Rational Thinking.
        
        Formula: reduce(day + sum(letters_of_given_name)) with master numbers
        
        Returns:
            int: Rational Thinking number
        """
        name_parts = self._split_name_parts()
        if not name_parts:
            return 0
            
        given_name = name_parts[-1]  # Last part (given name)
        given_name_sum = sum(
            self.ALPHABET.get(char.upper(), 0)
            for char in given_name
            if char.upper() in self.ALPHABET
        )
        
        return self.reduce_number_with_masters(self.day + given_name_sum)

    def calculate_age_milestones(self) -> List[int]:
        """
        Calculate Age Milestones.
        
        Returns:
            List[int]: List of age milestones
        """
        life_path = self.calculate_life_path()

        if life_path in self.MASTER_NUMBERS:
            start = 32  # 36 - 4
        else:
            start = 36 - life_path

        return [start, start + 9, start + 18, start + 27]

    def calculate_alignment_signals(self) -> Dict[str, int]:
        """
        Calculate Alignment Signals (Personal Year, Month, Day).
        
        Returns:
            Dict[str, int]: Dictionary with alignment signals
        """
        current_year = self.current_datetime.year
        current_month = self.current_datetime.month
        current_day = self.current_datetime.day

        # Personal Year
        personal_year = self.day + self.month + current_year

        if current_month < self.month or (current_month == self.month and current_day < self.day):
            personal_year -= 1
        
        personal_year = self.reduce_number_no_master(personal_year)

        # Personal Month
        personal_month = self.reduce_number_no_master(current_month + personal_year)

        # Personal Day
        personal_day = self.reduce_number_no_master(current_day + current_month + personal_year)

        return {
            "personal_year": personal_year,
            "personal_month": personal_month,
            "personal_day": personal_day
        }

    def get_personal_date_num(self) -> Dict[str, Union[int, str, List[int]]]:
        """
        Get comprehensive personal numerology calculations.

        Returns:
            Dictionary containing all calculated numerology numbers
        """
        return {
            "day_of_birth": self.dob_date.strftime("%d/%m/%Y"),
            "current_date": self.current_datetime.strftime("%d/%m/%Y"),
            "life_path": self.calculate_life_path(),
            "life_purpose": self.calculate_life_purpose(),
            "balance": self.calculate_balance(),
            "soul": self.calculate_soul(),
            "personality": self.calculate_personality(),
            "birth_day": self.calculate_birth_day(),
            "subconscious_strength": self.calculate_subconscious_strength(),
            "maturity": self.calculate_maturity(),
            "missing_aspects": list(self.get_missing_aspects()),
            "shadow_challenge_code": self.check_karmic_debt(),
            "passion": self.calculate_passion(),
            "societal_adaptability_index": self.get_societal_adaptability_index(),
            "emotional_response_style": self.calculate_emotional_response_style(),
            "lifepath_life_purpose_link": self.calculate_link_connection(),
            "soul_personality_link": self.calculate_soul_personality_link(),
            "milestone_phase": self.calculate_milestone_phase(),
            "challenge": self.calculate_challenge(),
            "rational_thinking": self.calculate_rational_thinking(),
            "age_milestones": self.calculate_age_milestones(),
            "alignment_signals": self.calculate_alignment_signals()
        }
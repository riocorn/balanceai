export type IndiaLocation = {
  state: string;
  type: "state" | "ut";
  cities: string[];
};

export const INDIA_LOCATIONS: IndiaLocation[] = [
  {
    state: "Andhra Pradesh", type: "state",
    cities: ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Kurnool", "Rajahmundry", "Tirupati", "Kakinada", "Kadapa", "Anantapur", "Eluru", "Ongole", "Vizianagaram", "Srikakulam", "Chittoor"],
  },
  {
    state: "Arunachal Pradesh", type: "state",
    cities: ["Itanagar", "Naharlagun", "Pasighat", "Namsai", "Bomdila", "Ziro", "Along", "Tezu", "Aalo", "Changlang"],
  },
  {
    state: "Assam", type: "state",
    cities: ["Guwahati", "Dibrugarh", "Silchar", "Jorhat", "Nagaon", "Tinsukia", "Tezpur", "Bongaigaon", "Dhubri", "North Lakhimpur", "Sivasagar", "Goalpara", "Barpeta", "Karimganj"],
  },
  {
    state: "Bihar", type: "state",
    cities: ["Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Purnia", "Darbhanga", "Bihar Sharif", "Arrah", "Begusarai", "Katihar", "Munger", "Chhapra", "Danapur", "Bettiah", "Saharsa", "Sasaram", "Hajipur", "Dehri", "Siwan", "Motihari"],
  },
  {
    state: "Chhattisgarh", type: "state",
    cities: ["Raipur", "Bhilai", "Bilaspur", "Korba", "Durg", "Rajnandgaon", "Jagdalpur", "Raigarh", "Ambikapur", "Dhamtari", "Mahasamund", "Bemetara"],
  },
  {
    state: "Goa", type: "state",
    cities: ["Panaji", "Vasco da Gama", "Margao", "Mapusa", "Ponda", "Bicholim", "Curchorem", "Sanquelim", "Quepem", "Canacona"],
  },
  {
    state: "Gujarat", type: "state",
    cities: ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", "Jamnagar", "Junagadh", "Gandhinagar", "Anand", "Navsari", "Morbi", "Nadiad", "Surendranagar", "Bharuch", "Mehsana", "Bhuj", "Porbandar", "Valsad", "Amreli", "Godhra"],
  },
  {
    state: "Haryana", type: "state",
    cities: ["Faridabad", "Gurugram", "Panipat", "Ambala", "Yamunanagar", "Rohtak", "Hisar", "Karnal", "Sonipat", "Panchkula", "Bhiwani", "Sirsa", "Bahadurgarh", "Rewari", "Kaithal", "Palwal", "Hansi", "Jhajjar", "Jind", "Thanesar"],
  },
  {
    state: "Himachal Pradesh", type: "state",
    cities: ["Shimla", "Solan", "Dharamsala", "Mandi", "Palampur", "Baddi", "Nahan", "Kullu", "Chamba", "Una", "Bilaspur", "Hamirpur", "Kangra", "Manali"],
  },
  {
    state: "Jharkhand", type: "state",
    cities: ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro", "Deoghar", "Hazaribagh", "Giridih", "Ramgarh", "Medininagar", "Chirkunda", "Phusro", "Dumka"],
  },
  {
    state: "Karnataka", type: "state",
    cities: ["Bengaluru", "Mysuru", "Hubballi", "Mangaluru", "Belagavi", "Kalaburagi", "Davanagere", "Ballari", "Shivamogga", "Tumakuru", "Raichur", "Bidar", "Vijayapura", "Hassan", "Udupi", "Dharwad", "Chitradurga", "Mandya", "Chikkamagaluru", "Bagalkot"],
  },
  {
    state: "Kerala", type: "state",
    cities: ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Kollam", "Palakkad", "Alappuzha", "Malappuram", "Kannur", "Kottayam", "Kasaragod", "Pathanamthitta", "Idukki", "Wayanad"],
  },
  {
    state: "Madhya Pradesh", type: "state",
    cities: ["Indore", "Bhopal", "Jabalpur", "Gwalior", "Ujjain", "Sagar", "Ratlam", "Satna", "Dewas", "Murwara", "Chhindwara", "Rewa", "Burhanpur", "Khandwa", "Bhind", "Shivpuri", "Vidisha", "Sehore", "Hoshangabad", "Itarsi"],
  },
  {
    state: "Maharashtra", type: "state",
    cities: ["Mumbai", "Pune", "Nagpur", "Nashik", "Thane", "Aurangabad (Chhatrapati Sambhajinagar)", "Solapur", "Kolhapur", "Amravati", "Nanded", "Sangli", "Malegaon", "Jalgaon", "Akola", "Latur", "Dhule", "Ahmednagar", "Chandrapur", "Parbhani", "Ichalkaranji"],
  },
  {
    state: "Manipur", type: "state",
    cities: ["Imphal", "Thoubal", "Bishnupur", "Churachandpur", "Kakching", "Ukhrul", "Senapati", "Tamenglong"],
  },
  {
    state: "Meghalaya", type: "state",
    cities: ["Shillong", "Tura", "Jowai", "Nongstoin", "Baghmara", "Resubelpara", "Nongpoh"],
  },
  {
    state: "Mizoram", type: "state",
    cities: ["Aizawl", "Lunglei", "Saiha", "Champhai", "Serchhip", "Kolasib", "Lawngtlai", "Mamit"],
  },
  {
    state: "Nagaland", type: "state",
    cities: ["Kohima", "Dimapur", "Mokokchung", "Tuensang", "Wokha", "Zunheboto", "Phek", "Mon"],
  },
  {
    state: "Odisha", type: "state",
    cities: ["Bhubaneswar", "Cuttack", "Rourkela", "Brahmapur", "Sambalpur", "Puri", "Balasore", "Baripada", "Bhadrak", "Jharsuguda", "Rayagada", "Angul", "Paradip", "Kendujhar", "Kendrapara"],
  },
  {
    state: "Punjab", type: "state",
    cities: ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda", "Hoshiarpur", "Mohali", "Batala", "Pathankot", "Moga", "Abohar", "Malerkotla", "Khanna", "Phagwara", "Muktsar", "Barnala", "Rajpura", "Firozpur", "Kapurthala"],
  },
  {
    state: "Rajasthan", type: "state",
    cities: ["Jaipur", "Jodhpur", "Kota", "Bikaner", "Ajmer", "Udaipur", "Bhilwara", "Alwar", "Bharatpur", "Sikar", "Pali", "Sri Ganganagar", "Tonk", "Hanumangarh", "Dausa", "Churu", "Sawai Madhopur", "Nagaur", "Jhunjhunu", "Baran"],
  },
  {
    state: "Sikkim", type: "state",
    cities: ["Gangtok", "Namchi", "Mangan", "Gyalshing", "Rangpo", "Jorethang"],
  },
  {
    state: "Tamil Nadu", type: "state",
    cities: ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", "Tirunelveli", "Tiruppur", "Vellore", "Thoothukudi", "Dindigul", "Thanjavur", "Ranipet", "Sivakasi", "Karur", "Udhagamandalam (Ooty)", "Hosur", "Nagercoil", "Kumbakonam", "Pollachi", "Rajapalayam"],
  },
  {
    state: "Telangana", type: "state",
    cities: ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Ramagundam", "Khammam", "Mahbubnagar", "Nalgonda", "Adilabad", "Suryapet", "Miryalaguda", "Jagtial", "Bhongir", "Mancherial", "Siddipet"],
  },
  {
    state: "Tripura", type: "state",
    cities: ["Agartala", "Dharmanagar", "Udaipur", "Kailasahar", "Belonia", "Sabroom", "Ambassa"],
  },
  {
    state: "Uttar Pradesh", type: "state",
    cities: ["Lucknow", "Kanpur", "Agra", "Varanasi", "Meerut", "Prayagraj", "Ghaziabad", "Bareilly", "Aligarh", "Moradabad", "Saharanpur", "Gorakhpur", "Firozabad", "Jhansi", "Mathura", "Rampur", "Shahjahanpur", "Muzaffarnagar", "Noida", "Faizabad (Ayodhya)", "Hapur", "Etawah", "Mirzapur", "Bulandshahr", "Sambhal", "Amroha", "Hardoi", "Fatehpur", "Raebareli", "Sitapur"],
  },
  {
    state: "Uttarakhand", type: "state",
    cities: ["Dehradun", "Haridwar", "Roorkee", "Haldwani", "Rudrapur", "Kashipur", "Rishikesh", "Kotdwar", "Ramnagar", "Pithoragarh", "Almora", "Nainital", "Mussoorie", "Tehri"],
  },
  {
    state: "West Bengal", type: "state",
    cities: ["Kolkata", "Asansol", "Siliguri", "Durgapur", "Bardhaman", "Malda", "Barasat", "Krishnanagar", "Howrah", "Medinipur", "Kharagpur", "Haldia", "Raiganj", "Jalpaiguri", "Cooch Behar", "Bankura", "Purulia", "Baharampur", "Alipurduar", "Darjeeling"],
  },
  // Union Territories
  {
    state: "Delhi (NCT)", type: "ut",
    cities: ["New Delhi", "Old Delhi", "Dwarka", "Rohini", "Janakpuri", "Lajpat Nagar", "Saket", "Pitampura", "Preet Vihar", "Noida Extension", "Shahdara", "Karol Bagh", "Connaught Place", "Vasant Kunj", "Mayur Vihar"],
  },
  {
    state: "Jammu and Kashmir", type: "ut",
    cities: ["Srinagar", "Jammu", "Anantnag", "Sopore", "Baramulla", "Kathua", "Udhampur", "Punch", "Rajouri", "Kupwara", "Pulwama"],
  },
  {
    state: "Ladakh", type: "ut",
    cities: ["Leh", "Kargil", "Diskit", "Padum"],
  },
  {
    state: "Chandigarh", type: "ut",
    cities: ["Chandigarh", "Manimajra", "Panchkula", "Mohali"],
  },
  {
    state: "Puducherry", type: "ut",
    cities: ["Puducherry", "Karaikal", "Mahe", "Yanam"],
  },
  {
    state: "Andaman and Nicobar Islands", type: "ut",
    cities: ["Port Blair", "Diglipur", "Rangat", "Car Nicobar"],
  },
  {
    state: "Dadra and Nagar Haveli and Daman and Diu", type: "ut",
    cities: ["Silvassa", "Daman", "Diu", "Amli"],
  },
  {
    state: "Lakshadweep", type: "ut",
    cities: ["Kavaratti", "Agatti", "Amini", "Andrott"],
  },
];

export const STATE_LIST = INDIA_LOCATIONS.map((l) => l.state);

export const getCities = (stateName: string): string[] =>
  INDIA_LOCATIONS.find((l) => l.state === stateName)?.cities ?? [];
